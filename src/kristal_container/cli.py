"""Small CLI with structured output and no secrets in process arguments."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

from . import Container, ContainerError, Credentials, Protection, __version__, inspect_header, pack
from .archive import inventory
from .common import Limits
from .errors import PolicyError
from .filesystem import atomic_output
from .keys import generate_key, load_key, save_key


def _password(fd, prompt, *, confirm=False):
    if fd is not None:
        with os.fdopen(os.dup(fd), "rb") as source:
            raw = source.read(4097)
        if len(raw) > 4096:
            raise PolicyError("Password input exceeds policy")
        value = raw.decode("utf-8").removesuffix("\n").removesuffix("\r")
    else:
        if not sys.stdin.isatty():
            raise PolicyError("Use an explicit password file descriptor in non-interactive mode")
        value = getpass.getpass(prompt)
        if confirm and value != getpass.getpass("Repeat password: "):
            raise PolicyError("Passwords do not match")
    return value


def _key_password(args):
    if not hasattr(args, "_key_password_cache"):
        args._key_password_cache = _password(args.key_password_fd, "Private-key password: ")
    return args._key_password_cache


def _load(args, attribute, kind, *, private=False):
    path = getattr(args, attribute, None)
    if path is None:
        return None
    return load_key(path, kind, password=_key_password(args) if private else None)


def _protection(args, *, new=False):
    mode = args.mode
    recipients = tuple(load_key(p, "recipient") for p in args.recipient)
    recovery = _load(args, "recovery_key", "recovery")
    factor = _load(args, "factor_key", "factor")
    if mode == "open":
        if recipients or recovery or factor:
            raise PolicyError("Open mode cannot have access keys")
        return Protection()
    if mode == "recipient" and not recipients:
        raise PolicyError("Recipient mode requires at least one recipient")
    if mode == "recipient" and factor is not None:
        raise PolicyError("A factor requires password-factor mode")
    if mode != "recipient" and recipients:
        raise PolicyError(
            "Recipient slots are alternative access; choose recipient mode explicitly"
        )
    if mode == "password-factor" and factor is None:
        raise PolicyError("Password-factor mode requires a factor key")
    if mode == "password" and factor is not None:
        raise PolicyError("Use password-factor mode for an additional factor")
    password = None
    if mode in ("password", "password-factor"):
        fd = args.new_password_fd if new else args.password_fd
        password = _password(fd, "New container password: ", confirm=True)
    return Protection(password=password, recipients=recipients, factor=factor, recovery=recovery)


def _credentials(args):
    password = None
    if args.password or args.password_fd is not None:
        password = _password(args.password_fd, "Container password: ")
    return Credentials(
        password=password,
        identity=_load(args, "identity", "identity", private=True),
        factor=_load(args, "unlock_factor", "factor"),
        recovery=_load(args, "unlock_recovery", "recovery"),
    )


def _reader(args):
    return Container(
        args.container,
        credentials=_credentials(args),
        trusted_signers=tuple(load_key(p, "verify") for p in args.trust),
        require_signature=args.require_signature,
        require_encrypted=args.require_encrypted,
        expected_sha256=args.expected_sha256,
    )


def _access(parser):
    parser.add_argument(
        "--password", action="store_true", help="Prompt for the existing container password"
    )
    parser.add_argument(
        "--password-fd", type=int, help="Read password from a descriptor, never an argument"
    )
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--key-password-fd", type=int)
    parser.add_argument("--unlock-factor", type=Path)
    parser.add_argument("--unlock-recovery", type=Path)
    parser.add_argument(
        "--trust",
        type=Path,
        action="append",
        default=[],
        help="Trusted signer public key; implies required signature",
    )
    parser.add_argument("--require-signature", action="store_true")
    parser.add_argument("--require-encrypted", action="store_true")
    parser.add_argument(
        "--expected-sha256", help="Physical file digest obtained from a trusted external source"
    )


def _protect(parser):
    parser.add_argument(
        "--mode", required=True, choices=["open", "password", "password-factor", "recipient"]
    )
    parser.add_argument("--recipient", type=Path, action="append", default=[])
    parser.add_argument(
        "--recovery-key", type=Path, help="Previously generated, separately stored recovery key"
    )
    parser.add_argument(
        "--factor-key", type=Path, help="Copyable second secret, NOT a hardware authenticator"
    )
    parser.add_argument("--overwrite", action="store_true")


def parser():
    root = argparse.ArgumentParser(
        prog="kristal-container", description="Verified, uncompressed .kristal containers"
    )
    root.add_argument("--version", action="version", version=__version__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities", help="Machine-readable supported and unsupported profiles")
    p = sub.add_parser("plan", help="List files selected for packaging; no writes")
    p.add_argument("source", type=Path)
    p.add_argument(
        "--include",
        action="append",
        help="Exact relative file; repeat to select an explicit subset",
    )
    p.add_argument("--allow-sensitive", action="store_true")
    p = sub.add_parser(
        "keygen", help="Generate a typed key; private identity/signing keys are encrypted"
    )
    p.add_argument("kind", choices=["identity", "signing", "recovery", "factor"])
    p.add_argument("output", type=Path)
    p.add_argument("--public", type=Path, help="Required for identity/signing keys")
    p.add_argument("--key-password-fd", type=int)
    p = sub.add_parser("pack", help="Build and verify a new immutable snapshot")
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    _protect(p)
    p.add_argument("--password-fd", type=int)
    p.add_argument("--key-password-fd", type=int)
    p.add_argument("--include", action="append")
    p.add_argument("--allow-sensitive", action="store_true")
    p.add_argument("--signing-key", type=Path)
    p = sub.add_parser("inspect", help="Read UNVERIFIED public header only")
    p.add_argument("container", type=Path)
    for name in ("verify", "list", "export", "extract", "rewrap"):
        p = sub.add_parser(name)
        p.add_argument("container", type=Path)
        _access(p)
        if name == "export":
            p.add_argument("member")
            p.add_argument("output", type=Path)
            p.add_argument("--allow-plaintext", action="store_true", required=True)
        elif name == "extract":
            p.add_argument("output", type=Path)
            p.add_argument("--allow-plaintext", action="store_true", required=True)
        elif name == "rewrap":
            p.add_argument("output", type=Path)
            _protect(p)
            p.add_argument("--new-password-fd", type=int)
            p.add_argument("--allow-plaintext", action="store_true")
    return root


def capabilities():
    return {
        "format": "kristal.container-capabilities/1",
        "version": __version__,
        "container_format": "kristal.container/1",
        "compression": "none",
        "implemented": [
            "open",
            "password",
            "password-factor-secret",
            "x25519-recipient",
            "recovery-secret",
            "ed25519-signature",
            "encrypted-staging",
            "rewrap",
        ],
        "unsupported": [
            "native-tpm",
            "webauthn-prf",
            "managed-kms",
            "post-quantum",
            "threshold-recovery",
        ],
        "independent_security_audit": False,
    }


def run(args):
    if args.command == "capabilities":
        return capabilities()
    if args.command == "plan":
        files = inventory(
            args.source,
            tuple(args.include) if args.include else None,
            args.allow_sensitive,
            Limits(),
        )
        return {
            "files": [{"path": p, "size": stamp[2]} for p, _, stamp in files],
            "total_bytes": sum(stamp[2] for _, _, stamp in files),
            "written": False,
        }
    if args.command == "keygen":
        private = args.kind in ("identity", "signing")
        if private != (args.public is not None):
            raise PolicyError(
                "Identity/signing keys require --public; bearer secrets must not use it"
            )
        if args.public is not None and args.public.absolute() == args.output.absolute():
            raise PolicyError("Private and public paths must differ")
        for path in (args.output, args.public):
            if path is not None and (path.exists() or not path.parent.is_dir()):
                raise PolicyError("Key destination must be new with an existing parent")
        password = (
            _password(args.key_password_fd, "New private-key password: ", confirm=True)
            if private
            else None
        )
        secret, public = generate_key(args.kind)
        save_key(args.output, args.kind, secret, password=password)
        if public is not None:
            save_key(args.public, "recipient" if args.kind == "identity" else "verify", public)
        return {"generated": args.kind, "secret_printed": False}
    if args.command == "pack":
        protection = _protection(args)
        signing = _load(args, "signing_key", "signing", private=True)
        return pack(
            args.source,
            args.output,
            protection=protection,
            selected=tuple(args.include) if args.include else None,
            signing_key=signing,
            allow_sensitive=args.allow_sensitive,
            overwrite=args.overwrite,
        )
    if args.command == "inspect":
        return inspect_header(args.container)
    with _reader(args) as container:
        if args.command == "verify":
            return container.report
        if args.command == "list":
            return {"verification": container.report, "files": container.list()}
        if args.command == "export":
            with atomic_output(args.output) as output:
                container.copy_to(args.member, output)
            return {"exported": True, "plaintext": True}
        if args.command == "extract":
            container.extract(args.output)
            return {"extracted": True, "plaintext": True, "file_count": len(container.list())}
        if args.command == "rewrap":
            container.rewrap(
                args.output,
                protection=_protection(args, new=True),
                overwrite=args.overwrite,
                allow_plaintext=args.allow_plaintext,
            )
            return {"rewrapped": True, "inner_archive_preserved": True, "old_copies_revoked": False}
    raise PolicyError("Unknown operation")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        print(json.dumps(run(args), ensure_ascii=True, sort_keys=True))
        return 0
    except ContainerError as exc:
        print(
            json.dumps({"error": exc.code, "message": str(exc)}, ensure_ascii=True), file=sys.stderr
        )
        return 2
    except (OSError, UnicodeError, ValueError) as exc:
        # Avoid reflecting filesystem paths, credentials or hostile strings.
        print(
            json.dumps({"error": "operation-failed", "message": type(exc).__name__}),
            file=sys.stderr,
        )
        return 3
    except KeyboardInterrupt:
        print('{"error":"cancelled"}', file=sys.stderr)
        return 130
