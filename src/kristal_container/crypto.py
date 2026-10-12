"""Versioned cryptographic profile. All envelope metadata is stream-authenticated."""

from __future__ import annotations

import hashlib
import hmac
import os
import struct
from dataclasses import dataclass, field

from argon2.low_level import Type, hash_secret_raw
from nacl import bindings as sodium
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, PublicKey, SealedBox

from .common import (
    CHUNK,
    FORMAT,
    HEADER_MAX,
    MAGIC,
    b64,
    canonical,
    fields,
    parse_json,
    read_exact,
    unb64,
)
from .errors import AccessError, FormatError, IntegrityError, PolicyError, UnsupportedError
from .providers import FactorProvider, RecipientResolver

PROFILE = "xchacha20poly1305-secretstream-v1"
KDF = {"name": "argon2id", "version": 19, "memory_kib": 65536, "iterations": 3, "parallelism": 4}


@dataclass(frozen=True)
class Protection:
    """OR between slots; AND within the password+factor slot.

    recovery and factor are independently generated 32-byte secrets. Neither is
    a human password. A factor file is copyable and is not a hardware authenticator.
    """

    password: str | None = field(default=None, repr=False)
    factor: bytes | None = field(default=None, repr=False)
    factor_provider: FactorProvider | None = field(default=None, repr=False)
    recipients: tuple[bytes, ...] = ()
    recovery: bytes | None = field(default=None, repr=False)

    @property
    def encrypted(self):
        return self.password is not None or bool(self.recipients) or self.recovery is not None

    def validate(self):
        if (self.factor is not None or self.factor_provider is not None) and self.password is None:
            raise PolicyError("A factor requires a password")
        if self.factor is not None and self.factor_provider is not None:
            raise PolicyError("Choose exactly one factor source")
        for secret in (self.factor, self.recovery):
            if secret is not None and (not isinstance(secret, bytes) or len(secret) != 32):
                raise PolicyError("Factor/recovery keys must be 32 random bytes")
        if self.password is not None:
            if not isinstance(self.password, str) or not 15 <= len(self.password) <= 1024:
                raise PolicyError("Use a password of 15 to 1024 characters")
            if len(self.password.encode("utf-8")) > 4096:
                raise PolicyError("Password exceeds byte limit")
        if len(self.recipients) > 14 or len(set(self.recipients)) != len(self.recipients):
            raise PolicyError("At most 14 distinct recipients")
        for key in self.recipients:
            if not isinstance(key, bytes) or len(key) != 32:
                raise PolicyError("Recipient public key must be 32 bytes")
        if self.factor is not None and self.factor == self.recovery:
            raise PolicyError("Recovery and factor secrets must be independent")


@dataclass(frozen=True)
class Credentials:
    password: str | None = field(default=None, repr=False)
    factor: bytes | None = field(default=None, repr=False)
    factor_provider: FactorProvider | None = field(default=None, repr=False)
    recipient_resolver: RecipientResolver | None = field(default=None, repr=False)
    allowed_recipient_ids: tuple[str, ...] = ()
    identity: bytes | None = field(default=None, repr=False)
    recovery: bytes | None = field(default=None, repr=False)


def _hkdf(ikm: bytes, salt: bytes, info: bytes) -> bytes:
    """RFC 5869 HKDF-SHA256, exactly one 32-byte output block."""
    prk = hmac.digest(salt, ikm, "sha256")
    return hmac.digest(prk, info + b"\x01", "sha256")


def _password_key(password: str, salt: bytes, factor: bytes | None, cid: bytes) -> bytes:
    if (
        not isinstance(password, str)
        or not 1 <= len(password) <= 1024
        or len(password.encode("utf-8")) > 4096
    ):
        raise AccessError("Invalid credentials")
    derived = hash_secret_raw(password.encode("utf-8"), salt, 3, 65536, 4, 32, Type.ID, version=19)
    if factor is not None:
        if not isinstance(factor, bytes) or len(factor) != 32:
            raise AccessError("Invalid credentials")
        return _hkdf(derived + factor, cid, b"kristal/password-factor/v1")
    return _hkdf(derived, cid, b"kristal/password/v1")


def _wrap(key: bytes, descriptor: dict, root: bytes, cid: bytes) -> dict:
    nonce = os.urandom(24)
    descriptor = {**descriptor, "nonce": b64(nonce)}
    aad = b"kristal/keyslot/v1\x00" + cid + canonical(descriptor)
    return {
        **descriptor,
        "wrapped": b64(sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(root, aad, nonce, key)),
    }


def make_header(protection: Protection):
    protection.validate()
    if not protection.encrypted:
        return {"format": FORMAT, "mode": "open"}, None
    root = os.urandom(32)
    cid = os.urandom(16)
    slots = []
    if protection.password is not None:
        salt = os.urandom(16)
        factor = (
            protection.factor_provider.derive(cid)
            if protection.factor_provider is not None
            else protection.factor
        )
        if protection.factor_provider is not None and (
            not isinstance(factor, bytes) or len(factor) != 32
        ):
            raise PolicyError("Factor provider returned an invalid secret")
        kind = "password-factor" if factor is not None else "password"
        descriptor = {"type": kind, "kdf": KDF, "salt": b64(salt)}
        key = _password_key(protection.password, salt, factor, cid)
        slots.append(_wrap(key, descriptor, root, cid))
    for public in protection.recipients:
        try:
            wrapped = SealedBox(PublicKey(public)).encrypt(cid + root)
        except (CryptoError, ValueError) as exc:
            raise PolicyError("Invalid recipient public key") from exc
        slots.append(
            {
                "type": "x25519",
                "key_id": hashlib.sha256(public).hexdigest(),
                "wrapped": b64(wrapped),
            }
        )
    if protection.recovery is not None:
        key = _hkdf(protection.recovery, cid, b"kristal/recovery/v1")
        slots.append(_wrap(key, {"type": "recovery"}, root, cid))
    state = sodium.crypto_secretstream_xchacha20poly1305_state()
    stream_header = sodium.crypto_secretstream_xchacha20poly1305_init_push(state, root)
    header = {
        "format": FORMAT,
        "mode": "encrypted",
        "profile": PROFILE,
        "id": b64(cid),
        "stream": b64(stream_header),
        "slots": slots,
    }
    return header, state


def validate_header(header):
    if not isinstance(header, dict) or header.get("format") != FORMAT:
        raise UnsupportedError("Unsupported container version")
    if header.get("mode") == "open":
        fields(header, {"format", "mode"})
        return
    fields(header, {"format", "mode", "profile", "id", "stream", "slots"})
    if header["mode"] != "encrypted" or header["profile"] != PROFILE:
        raise UnsupportedError("Unsupported protection profile")
    unb64(header["id"], 16)
    unb64(header["stream"], 24)
    slots = header["slots"]
    if not isinstance(slots, list) or not 1 <= len(slots) <= 16:
        raise FormatError("Invalid slot count")
    seen = set()
    for slot in slots:
        if not isinstance(slot, dict):
            raise FormatError("Invalid key slot")
        kind = slot.get("type")
        if kind in ("password", "password-factor"):
            fields(slot, {"type", "kdf", "salt", "nonce", "wrapped"})
            if canonical(slot["kdf"]) != canonical(KDF):
                raise UnsupportedError("Unsupported or excessive password KDF parameters")
            unb64(slot["salt"], 16)
            unb64(slot["nonce"], 24)
            unb64(slot["wrapped"], 48)
            identifier = "password"
        elif kind == "recovery":
            fields(slot, {"type", "nonce", "wrapped"})
            unb64(slot["nonce"], 24)
            unb64(slot["wrapped"], 48)
            identifier = kind
        elif kind == "x25519":
            fields(slot, {"type", "key_id", "wrapped"})
            kid = slot["key_id"]
            if (
                not isinstance(kid, str)
                or len(kid) != 64
                or any(c not in "0123456789abcdef" for c in kid)
            ):
                raise FormatError("Invalid recipient identifier")
            unb64(slot["wrapped"], 96)
            identifier = kid
        else:
            raise UnsupportedError("Unknown key slot; no fallback permitted")
        if identifier in seen:
            raise FormatError("Duplicate key slot")
        seen.add(identifier)


def unlock(header, credentials: Credentials, header_digest: bytes):
    cid = unb64(header["id"], 16)
    for slot in header["slots"]:
        kind = slot["type"]
        try:
            if kind == "x25519":
                if (
                    credentials.recipient_resolver is not None
                    and slot["key_id"] in credentials.allowed_recipient_ids
                ):
                    plain = credentials.recipient_resolver.unwrap(
                        key_id=slot["key_id"],
                        container_id=cid,
                        wrapped=unb64(slot["wrapped"], 96),
                        header_sha256=header_digest,
                    )
                    if plain is not None:
                        if (
                            not isinstance(plain, bytes)
                            or len(plain) != 48
                            or not hmac.compare_digest(plain[:16], cid)
                        ):
                            raise AccessError("Recipient provider returned an invalid result")
                        return plain[16:]
                if credentials.identity is None:
                    continue
                if len(credentials.identity) != 32:
                    raise AccessError("Invalid credentials")
                identity = PrivateKey(credentials.identity)
                if hashlib.sha256(bytes(identity.public_key)).hexdigest() != slot["key_id"]:
                    continue
                plain = SealedBox(identity).decrypt(unb64(slot["wrapped"], 96))
                if not hmac.compare_digest(plain[:16], cid):
                    continue
                return plain[16:]
            if kind in ("password", "password-factor"):
                if credentials.password is None or (
                    kind == "password-factor"
                    and credentials.factor is None
                    and credentials.factor_provider is None
                ):
                    continue
                factor = None
                if kind == "password-factor":
                    factor = (
                        credentials.factor_provider.derive(cid)
                        if credentials.factor_provider is not None
                        else credentials.factor
                    )
                    if not isinstance(factor, bytes) or len(factor) != 32:
                        raise AccessError("Factor provider returned an invalid secret")
                key = _password_key(credentials.password, unb64(slot["salt"], 16), factor, cid)
            elif kind == "recovery":
                if credentials.recovery is None:
                    continue
                if len(credentials.recovery) != 32:
                    raise AccessError("Invalid credentials")
                key = _hkdf(credentials.recovery, cid, b"kristal/recovery/v1")
            else:
                raise UnsupportedError("Unsupported key slot")
            descriptor = {k: v for k, v in slot.items() if k != "wrapped"}
            aad = b"kristal/keyslot/v1\x00" + cid + canonical(descriptor)
            return sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(
                unb64(slot["wrapped"], 48), aad, unb64(slot["nonce"], 24), key
            )
        except CryptoError:
            continue
    raise AccessError("Credentials rejected or key envelope damaged")


def read_header(stream):
    if read_exact(stream, 8) != MAGIC:
        raise FormatError("Not a Kristal container v1")
    length = struct.unpack(">I", read_exact(stream, 4))[0]
    if not 1 <= length <= HEADER_MAX:
        raise FormatError("Invalid header length")
    raw = read_exact(stream, length)
    header = parse_json(raw, HEADER_MAX)
    validate_header(header)
    return header, hashlib.sha256(MAGIC + struct.pack(">I", length) + raw).digest()


def write_envelope(archive, output, protection: Protection):
    header, state = make_header(protection)
    raw = canonical(header)
    if len(raw) > HEADER_MAX:
        raise PolicyError("Key envelope too large")
    prefix = MAGIC + struct.pack(">I", len(raw)) + raw
    output.write(prefix)
    archive.seek(0)
    if state is None:
        while data := archive.read(CHUNK):
            output.write(data)
        return
    aad = b"kristal/stream/v1\x00" + hashlib.sha256(prefix).digest()
    # Always an empty FINAL frame, even for exact multiples of CHUNK.
    while data := archive.read(CHUNK):
        cipher = sodium.crypto_secretstream_xchacha20poly1305_push(state, data, aad, 0)
        output.write(struct.pack(">I", len(cipher)))
        output.write(cipher)
    final = sodium.crypto_secretstream_xchacha20poly1305_push(state, b"", aad, 3)
    output.write(struct.pack(">I", len(final)))
    output.write(final)


def read_payload(stream, spool, header, header_digest, credentials: Credentials):
    if header["mode"] == "open":
        while data := stream.read(CHUNK):
            spool.write(data)
        spool.seal()
        return
    key = unlock(header, credentials, header_digest)
    state = sodium.crypto_secretstream_xchacha20poly1305_state()
    sodium.crypto_secretstream_xchacha20poly1305_init_pull(state, unb64(header["stream"], 24), key)
    aad = b"kristal/stream/v1\x00" + header_digest
    short_seen = False
    while True:
        length = struct.unpack(">I", read_exact(stream, 4))[0]
        if not 17 <= length <= CHUNK + 17:
            raise FormatError("Invalid encrypted frame length")
        try:
            data, tag = sodium.crypto_secretstream_xchacha20poly1305_pull(
                state, read_exact(stream, length), aad
            )
        except CryptoError as exc:
            raise IntegrityError("Encrypted stream authentication failed") from exc
        if tag == 3:
            if data or stream.read(1):
                raise FormatError("Invalid final frame or trailing bytes")
            break
        if tag != 0 or not data or short_seen:
            raise FormatError("Invalid stream framing")
        short_seen = len(data) < CHUNK
        spool.write(data)
    spool.seal()
