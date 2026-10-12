"""Thin Local Kit adapter. No subprocess, build, publication or activation."""

from __future__ import annotations

from .api import pack
from .common import Limits, PathSet
from .errors import FormatError, LimitError, PolicyError


def pack_read_surface(source, destination, projection: dict, *, limits=Limits(), **options):
    """Consume the existing kristal.github-read-surface/1.0 file projection.

    Byte assertions are verified against the exact packaged snapshot. References
    to external materialization blobs stay references; nothing is fetched. The
    caller, not this function, establishes the projection's provenance/authority.
    """
    if (
        not isinstance(projection, dict)
        or projection.get("format") != "kristal.github-read-surface/1.0"
    ):
        raise FormatError("Unsupported read-surface contract")
    if projection.get("ready") is not True or projection.get("errors") != []:
        raise PolicyError("Local Kit read surface is not ready")
    files = projection.get("files")
    if not isinstance(files, list) or len(files) > limits.max_files:
        raise LimitError("Invalid read-surface file count")
    expected = []
    seen = PathSet()
    for item in files:
        if not isinstance(item, dict):
            raise FormatError("Invalid read-surface member")
        path, size, sha = item.get("path"), item.get("size"), item.get("sha256")
        seen.add(path)
        if (
            type(size) is not int
            or size < 0
            or not isinstance(sha, str)
            or not sha.startswith("sha256:")
        ):
            raise FormatError("Invalid read-surface metadata")
        sha = sha.removeprefix("sha256:")
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise FormatError("Invalid read-surface digest")
        expected.append({"path": path, "size": size, "sha256": sha})
    if projection.get("file_count") != len(files) or projection.get("total_bytes") != sum(
        x["size"] for x in expected
    ):
        raise FormatError("Read-surface totals mismatch")
    if "selected" in options or "expected_members" in options:
        raise PolicyError("Cannot override read-surface membership")
    expected.sort(key=lambda x: x["path"])
    return pack(
        source,
        destination,
        selected=tuple(x["path"] for x in expected),
        expected_members=expected,
        limits=limits,
        **options,
    )
