"""Public API: verify completely before exposing names or bytes."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

from .archive import build_archive, verify_archive
from .common import CHUNK, Limits, portable_path
from .crypto import Credentials, Protection, read_header, read_payload, write_envelope
from .errors import IntegrityError, LimitError, PolicyError
from .filesystem import atomic_output, regular_input, reject_links, sync_directory
from .staging import EncryptedSpool


def pack(
    source: Path,
    destination: Path,
    *,
    protection=Protection(),
    selected=None,
    signing_key=None,
    allow_sensitive=False,
    overwrite=False,
    limits=Limits(),
    expected_members=None,
):
    source, destination = reject_links(Path(source)), reject_links(Path(destination))
    if destination.is_relative_to(source):
        raise PolicyError("Destination must be outside the source tree")
    protection.validate()
    with EncryptedSpool(limits.max_archive_bytes) as spool:
        manifest = build_archive(
            source,
            spool,
            selected=selected,
            signing_key=signing_key,
            allow_sensitive=allow_sensitive,
            limits=limits,
        )
        if expected_members is not None and manifest["files"] != expected_members:
            raise IntegrityError("Snapshot differs from the supplied read-surface projection")
        # Read back the exact snapshot before committing the final file.
        archive, _, report = verify_archive(spool, limits=limits)
        archive.close()
        with atomic_output(destination, overwrite=overwrite) as output:
            write_envelope(spool, output, protection)
    return {**report, "mode": "encrypted" if protection.encrypted else "open"}


class Container:
    """Verified, read-only snapshot; use as a context manager, not across threads.

    Names and members are available only after full structural, byte-integrity
    and requested trust-policy verification. No network access or execution.
    """

    def __init__(
        self,
        path: Path,
        *,
        credentials=Credentials(),
        limits=Limits(),
        trusted_signers=(),
        require_signature=False,
        require_encrypted=False,
        expected_sha256: str | None = None,
    ):
        self._spool = EncryptedSpool(limits.max_archive_bytes)
        self._archive = None
        self.limits = limits
        try:
            with regular_input(Path(path)) as source:
                if os.fstat(source.fileno()).st_size > limits.max_archive_bytes + 65548 + 21 * (
                    limits.max_archive_bytes // CHUNK + 2
                ):
                    raise LimitError("Container exceeds policy")
                # Hash the exact bytes subsequently consumed, including prefix.
                tracked = _HashingReader(source)
                header, header_digest = read_header(tracked)
                if require_encrypted and header["mode"] != "encrypted":
                    raise PolicyError("Encrypted container required by caller")
                read_payload(tracked, self._spool, header, header_digest, credentials)
                if expected_sha256 is not None and tracked.hash.hexdigest() != expected_sha256:
                    raise IntegrityError("Container does not match the expected physical digest")
                self._physical_digest = tracked.hash.hexdigest()
            self._archive, self._manifest, report = verify_archive(
                self._spool,
                limits=limits,
                trusted_signers=trusted_signers,
                require_signature=require_signature,
            )
            self._members = {record["path"]: record for record in self._manifest["files"]}
            self.report = {
                **report,
                "mode": header["mode"],
                "container_sha256": self._physical_digest,
            }
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self._archive is not None:
            self._archive.close()
        self._spool.close()

    def list(self):
        return [dict(record) for record in self._members.values()]

    def read(self, path: str):
        portable_path(path)
        if path not in self._members:
            raise PolicyError("Member is not present")
        if self._members[path]["size"] > self.limits.max_read_bytes:
            raise LimitError("Member too large for read(); use copy_to()")
        return self._archive.read(path)

    def copy_to(self, path: str, destination):
        """Explicit plaintext export to a caller-provided binary stream."""
        portable_path(path)
        if path not in self._members:
            raise PolicyError("Member is not present")
        with self._archive.open(path) as source:
            while data := source.read(CHUNK):
                destination.write(data)

    def extract(self, destination: Path):
        """Explicit plaintext extraction, private new directory, no overwrite.

        Reserve destination exclusively; clean it on failure. Unlike container
        writes this directory operation is not atomic and can leave partial data
        after process termination. It is never performed during normal reads.
        """
        destination = reject_links(Path(destination))
        if not destination.parent.is_dir():
            raise PolicyError("Destination parent must already exist")
        try:
            destination.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise PolicyError("Extraction destination must not exist") from exc
        try:
            for relative in self._members:
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with atomic_output(target) as output:
                    self.copy_to(relative, output)
            sync_directory(destination)
        except BaseException:
            shutil.rmtree(destination)
            raise

    def rewrap(
        self, destination: Path, *, protection: Protection, overwrite=False, allow_plaintext=False
    ):
        """Fresh content key and stream; keep exact inner archive and signatures.

        Existing copies are unaffected. This is not remote revocation.
        """
        protection.validate()
        if self.report["mode"] == "encrypted" and not protection.encrypted and not allow_plaintext:
            raise PolicyError("Removing encryption requires explicit allow_plaintext")
        with atomic_output(Path(destination), overwrite=overwrite) as output:
            write_envelope(self._spool, output, protection)


class _HashingReader:
    def __init__(self, source):
        self.source = source
        self.hash = hashlib.sha256()

    def read(self, n):
        data = self.source.read(n)
        self.hash.update(data)
        return data


def inspect_header(path: Path):
    """Only public claims; not verified, not a substitute for Container()."""
    with regular_input(Path(path)) as source:
        header, _ = read_header(source)
    return {
        "format": header["format"],
        "mode": header["mode"],
        "verified": False,
        "access_methods": [s["type"] for s in header.get("slots", [])],
    }
