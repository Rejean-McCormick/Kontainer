"""Strict serialization, portable names and bounded input handling."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass

from .errors import FormatError, LimitError, PolicyError

MAGIC = b"KRISTAL\x01"
FORMAT = "kristal.container/1"
MANIFEST = "_kristal/manifest.json"
CHUNK = 1024 * 1024
HEADER_MAX = 65536


@dataclass(frozen=True)
class Limits:
    max_files: int = 10000
    max_file_bytes: int = 8 * 1024**3
    max_total_bytes: int = 16 * 1024**3
    max_manifest_bytes: int = 8 * 1024**2
    max_central_directory_bytes: int = 16 * 1024**2
    max_read_bytes: int = 16 * 1024**2

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in vars(self).values()):
            raise ValueError("Limits must be positive integers")

    @property
    def max_archive_bytes(self):
        return self.max_total_bytes + self.max_manifest_bytes + 4096 * (self.max_files + 1)


def canonical(obj) -> bytes:
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise FormatError("Duplicate JSON member")
        out[key] = value
    return out


def parse_json(raw: bytes, maximum: int):
    if len(raw) > maximum:
        raise LimitError("JSON size exceeds policy")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(FormatError("Non-finite JSON")),
        )
        if canonical(value) != raw:
            raise FormatError("Non-canonical JSON")
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise FormatError("Invalid JSON") from exc


def fields(obj, required: set[str], optional: set[str] = frozenset()):
    if not isinstance(obj, dict) or not required <= obj.keys() or obj.keys() - required - optional:
        raise FormatError("Unexpected object fields")


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def unb64(value, size: int) -> bytes:
    if not isinstance(value, str) or len(value) != 4 * ((size + 2) // 3):
        raise FormatError("Invalid binary encoding length")
    try:
        raw = base64.b64decode(value, validate=True)
    except ValueError as exc:
        raise FormatError("Invalid base64") from exc
    if len(raw) != size or b64(raw) != value:
        raise FormatError("Non-canonical base64")
    return raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_exact(stream, length: int) -> bytes:
    data = stream.read(length)
    if len(data) != length:
        raise FormatError("Truncated input")
    return data


def portable_path(value: str, *, internal=False) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 1024:
        raise FormatError("Invalid path length")
    if unicodedata.normalize("NFC", value) != value:
        raise FormatError("Path must use Unicode NFC")
    if any(unicodedata.category(c).startswith("C") for c in value):
        raise FormatError("Control or format characters in path")
    if any(c in value for c in '\\:*?"<>|'):
        raise FormatError("Non-portable path")
    parts = value.split("/")
    for part in parts:
        if part in ("", ".", "..") or part.endswith((".", " ")) or len(part.encode("utf-8")) > 240:
            raise FormatError("Unsafe path component")
        stem = part.split(".")[0].upper()
        if stem in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} or re.fullmatch(
            r"(?:COM|LPT)[1-9¹²³]", stem
        ):
            raise FormatError("Reserved Windows path")
    if not internal and parts[0].casefold() == "_kristal":
        raise FormatError("Reserved container namespace")
    return value


class PathSet:
    """Reject aliases, case collisions and file/directory prefix collisions."""

    def __init__(self):
        self.files = set()
        self.dirs = set()
        self.spelling = {}

    def add(self, path: str, *, internal=False):
        portable_path(path, internal=internal)
        parts = path.split("/")
        for i in range(1, len(parts) + 1):
            spelling = "/".join(parts[:i])
            folded = spelling.casefold()
            if self.spelling.setdefault(folded, spelling) != spelling:
                raise FormatError("Case-colliding paths")
            if i < len(parts):
                if folded in self.files:
                    raise FormatError("File/directory collision")
                self.dirs.add(folded)
        folded = path.casefold()
        if folded in self.files or folded in self.dirs:
            raise FormatError("Duplicate or conflicting path")
        self.files.add(folded)


def reject_sensitive(path: str):
    parts = [p.casefold() for p in path.split("/")]
    blocked = {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".ssh",
        ".aws",
        ".azure",
    }
    leaf = parts[-1]
    if (
        any(p in blocked for p in parts)
        or leaf == ".env"
        or leaf.startswith(".env.")
        or leaf in {"credentials", "credentials.json", "id_rsa", "id_ed25519", "id_ecdsa"}
        or leaf.endswith((".pem", ".key", ".p12", ".pfx", ".kkey", ".ksecret"))
    ):
        raise PolicyError("Sensitive or development path requires explicit inclusion policy")
