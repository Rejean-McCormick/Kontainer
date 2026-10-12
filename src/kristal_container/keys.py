"""Typed key files. Private keys are encrypted at rest by default.

Raw factor/recovery secrets are explicit bearer credentials kept outside containers.
"""

from __future__ import annotations

import os
from pathlib import Path

from nacl import bindings as sodium
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from .common import b64, canonical, fields, parse_json, unb64
from .crypto import KDF, _password_key
from .errors import AccessError, FormatError, PolicyError
from .filesystem import atomic_output, regular_input

KEY_FORMAT = "kristal.key/1"


def generate_key(kind: str):
    if kind == "identity":
        key = PrivateKey.generate()
        return bytes(key), bytes(key.public_key)
    if kind == "signing":
        key = SigningKey.generate()
        return bytes(key), bytes(key.verify_key)
    if kind in ("recovery", "factor"):
        return os.urandom(32), None
    raise PolicyError("Unknown key purpose")


def save_key(path: Path, kind: str, secret: bytes, *, password: str | None = None):
    if (
        kind not in {"identity", "signing", "recipient", "verify", "recovery", "factor"}
        or len(secret) != 32
    ):
        raise PolicyError("Invalid key")
    if kind in ("identity", "signing") and password is None:
        raise PolicyError("Private identity/signing files require encryption")
    obj = {"format": KEY_FORMAT, "kind": kind}
    if password is None:
        obj["data"] = b64(secret)
    else:
        if not 15 <= len(password) <= 1024:
            raise PolicyError("Key password must contain 15 to 1024 characters")
        salt, nonce = os.urandom(16), os.urandom(24)
        obj.update({"kdf": KDF, "salt": b64(salt), "nonce": b64(nonce)})
        key = _password_key(password, salt, None, b"kristal-key-v1\x00\x00")
        obj["encrypted"] = b64(
            sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(
                secret, b"kristal/keyfile/v1\x00" + canonical(obj), nonce, key
            )
        )
    with atomic_output(path) as output:
        output.write(canonical(obj))


def load_key(path: Path, expected_kind: str, *, password: str | None = None):
    with regular_input(path) as source:
        obj = parse_json(source.read(4097), 4096)
    if (
        not isinstance(obj, dict)
        or obj.get("format") != KEY_FORMAT
        or obj.get("kind") != expected_kind
    ):
        raise FormatError("Wrong key file type")
    if "data" in obj:
        fields(obj, {"format", "kind", "data"})
        if expected_kind in ("identity", "signing"):
            raise PolicyError("Unencrypted private key files are forbidden")
        return unb64(obj["data"], 32)
    fields(obj, {"format", "kind", "kdf", "salt", "nonce", "encrypted"})
    if canonical(obj["kdf"]) != canonical(KDF):
        raise FormatError("Unsupported key KDF")
    salt, nonce, encrypted = (
        unb64(obj["salt"], 16),
        unb64(obj["nonce"], 24),
        unb64(obj["encrypted"], 48),
    )
    if password is None:
        raise AccessError("Key password required")
    key = _password_key(password, salt, None, b"kristal-key-v1\x00\x00")
    descriptor = {k: v for k, v in obj.items() if k != "encrypted"}
    try:
        return sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(
            encrypted, b"kristal/keyfile/v1\x00" + canonical(descriptor), nonce, key
        )
    except CryptoError as exc:
        raise AccessError("Key password rejected or key file damaged") from exc
