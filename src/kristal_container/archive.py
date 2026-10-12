"""Restricted ZIP64 STORE profile and signed byte manifest.

The package manifest describes physical bytes, never a Kristal Logical Commitment.
"""

from __future__ import annotations

import hashlib
import os
import stat
import struct
import zipfile
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from .common import (
    CHUNK,
    MANIFEST,
    Limits,
    PathSet,
    b64,
    canonical,
    fields,
    parse_json,
    portable_path,
    read_exact,
    reject_sensitive,
    unb64,
)
from .errors import FormatError, IntegrityError, LimitError, PolicyError
from .filesystem import regular_input, reject_links

MANIFEST_FORMAT = "kristal.container-manifest/1"
SIGN_DOMAIN = b"kristal/container-manifest/1\x00"


def _stamp(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def inventory(root: Path, selected: tuple[str, ...] | None, allow_sensitive: bool, limits: Limits):
    root = reject_links(root)
    if not root.is_dir():
        raise PolicyError("Source must be a directory")
    if selected is None:
        selected_list = []
        # Bound traversal as well as file count (empty-directory denial of service).
        visited = 0
        pending = [root]
        while pending:
            parent = pending.pop()
            with os.scandir(parent) as children:
                for entry in children:
                    visited += 1
                    if visited > limits.max_files * 8:
                        raise LimitError("Source traversal exceeds policy")
                    relative = Path(entry.path).relative_to(root).as_posix()
                    portable_path(relative)
                    if not allow_sensitive:
                        reject_sensitive(relative)
                    st = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
                        raise PolicyError("Source links/reparse points are forbidden")
                    if stat.S_ISDIR(st.st_mode):
                        pending.append(Path(entry.path))
                    elif stat.S_ISREG(st.st_mode):
                        selected_list.append(relative)
                    else:
                        raise PolicyError("Special source files are forbidden")
    else:
        selected_list = list(selected)
    if len(selected_list) > limits.max_files:
        raise LimitError("Too many source files")
    path_set = PathSet()
    files = []
    total = 0
    for relative in sorted(selected_list):
        path_set.add(relative)
        if not allow_sensitive:
            reject_sensitive(relative)
        path = reject_links(root / relative)
        st = path.stat()
        if not stat.S_ISREG(st.st_mode):
            raise PolicyError("Selected path must be a regular file")
        if st.st_size > limits.max_file_bytes:
            raise LimitError("Source file exceeds policy")
        total += st.st_size
        if total > limits.max_total_bytes:
            raise LimitError("Source tree exceeds policy")
        files.append((relative, path, _stamp(st)))
    return files


def _zip_info(path):
    info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100600 << 16
    return info


def build_archive(
    root, spool, *, selected=None, allow_sensitive=False, signing_key=None, limits=Limits()
):
    files = inventory(root, selected, allow_sensitive, limits)
    records = []
    # The spool is deliberately unseekable while writing, forcing descriptors.
    with zipfile.ZipFile(spool, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for relative, path, stamp in files:
            hasher = hashlib.sha256()
            length = 0
            with (
                regular_input(path) as source,
                archive.open(_zip_info(relative), "w", force_zip64=True) as dest,
            ):
                if _stamp(os.fstat(source.fileno())) != stamp:
                    raise PolicyError("Source changed during snapshot")
                while data := source.read(CHUNK):
                    length += len(data)
                    if length > stamp[2]:
                        raise PolicyError("Source grew during snapshot")
                    dest.write(data)
                    hasher.update(data)
                if length != stamp[2] or _stamp(os.fstat(source.fileno())) != stamp:
                    raise PolicyError("Source changed during snapshot")
            records.append({"path": relative, "size": length, "sha256": hasher.hexdigest()})
        manifest = {"format": MANIFEST_FORMAT, "files": records}
        if signing_key is not None:
            signer = SigningKey(signing_key)
            signature = signer.sign(SIGN_DOMAIN + canonical(manifest)).signature
            manifest["signature"] = {
                "algorithm": "ed25519",
                "public_key": b64(bytes(signer.verify_key)),
                "value": b64(signature),
            }
        raw = canonical(manifest)
        if len(raw) > limits.max_manifest_bytes:
            raise LimitError("Manifest exceeds policy")
        with archive.open(_zip_info(MANIFEST), "w", force_zip64=True) as dest:
            dest.write(raw)
    # Detect normal concurrent edits/deletions before publication. Hostile same-user
    # races are outside the filesystem trust boundary; see docs/THREAT_MODEL.md.
    if inventory(root, selected, allow_sensitive, limits) != files:
        raise PolicyError("Source tree changed during snapshot")
    spool.seal()
    return manifest


def _preflight(stream, limits):
    """Bound central directory before handing it to Python's ZIP parser."""
    stream.seek(0, 2)
    end = stream.tell()
    if end < 22 or end > limits.max_archive_bytes:
        raise LimitError("Archive size outside policy")
    stream.seek(end - 22)
    signature, disk, cd_disk, disk_count, count, size, offset, comment = struct.unpack(
        "<4s4H2LH", read_exact(stream, 22)
    )
    if signature != b"PK\x05\x06" or disk or cd_disk or comment or disk_count != count:
        raise FormatError("Unsupported ZIP trailer")
    trailer_start = end - 22
    locator_present = False
    if end >= 42:
        stream.seek(end - 42)
        locator_present = stream.read(4) == b"PK\x06\x07"
    if locator_present or count == 65535 or size == 0xFFFFFFFF or offset == 0xFFFFFFFF:
        legacy = count, size, offset
        if end < 98:
            raise FormatError("Truncated ZIP64 trailer")
        stream.seek(end - 42)
        sig, disk, zip64_offset, disks = struct.unpack("<4sLQL", read_exact(stream, 20))
        if sig != b"PK\x06\x07" or disk or disks != 1 or zip64_offset + 56 != end - 42:
            raise FormatError("Invalid ZIP64 locator")
        stream.seek(zip64_offset)
        record = struct.unpack("<4sQ2H2L4Q", read_exact(stream, 56))
        sig, record_size, made, needed, disk, cd_disk, disk_count, count, size, offset = record
        if (
            sig != b"PK\x06\x06"
            or record_size != 44
            or disk
            or cd_disk
            or disk_count != count
            or needed != 45
        ):
            raise FormatError("Invalid ZIP64 trailer")
        for small, large, sentinel in zip(
            legacy, (count, size, offset), (65535, 0xFFFFFFFF, 0xFFFFFFFF), strict=True
        ):
            if small != sentinel and small != large:
                raise FormatError("ZIP64 and legacy trailer disagree")
        trailer_start = zip64_offset
    if count < 1 or count > limits.max_files + 1 or size > limits.max_central_directory_bytes:
        raise LimitError("Central directory exceeds policy")
    if offset + size != trailer_start or offset < 0:
        raise FormatError("Invalid central directory extent")
    # Python zipfile does not bound its allocations using the declared count.
    # Count actual central records before allowing its parser to allocate objects.
    stream.seek(offset)
    consumed = 0
    actual = 0
    while consumed < size:
        raw = read_exact(stream, 46)
        if raw[:4] != b"PK\x01\x02":
            raise FormatError("Invalid central directory record")
        name_len, extra_len, comment_len = struct.unpack("<HHH", raw[28:34])
        length = 46 + name_len + extra_len + comment_len
        consumed += length
        actual += 1
        if actual > count or consumed > size or name_len > 1024 or extra_len > 28 or comment_len:
            raise FormatError("Central directory record exceeds declared bounds")
        read_exact(stream, length - 46)
    if consumed != size or actual != count:
        raise FormatError("Central directory count mismatch")
    stream.seek(0)
    return count, offset


def _extra(raw):
    """Only one well-formed ZIP64 extra field is allowed."""
    if not raw:
        return
    if len(raw) < 4:
        raise FormatError("Invalid ZIP extra")
    kind, length = struct.unpack("<HH", raw[:4])
    if kind != 1 or length not in (8, 16, 24) or length + 4 != len(raw):
        raise FormatError("Unsupported ZIP extra")


def _layout(stream, archive, expected_count, cd_offset, limits):
    infos = archive.infolist()
    if len(infos) != expected_count or archive.start_dir != cd_offset:
        raise FormatError("ZIP central directory mismatch")
    seen = PathSet()
    position = 0
    total = 0
    for info in infos:
        seen.add(info.filename, internal=info.filename == MANIFEST)
        if info.orig_filename != info.filename:
            raise FormatError("NUL in ZIP filename")
        if info.filename != MANIFEST and info.file_size > limits.max_file_bytes:
            raise LimitError("Member exceeds policy")
        if info.filename == MANIFEST and info.file_size > limits.max_manifest_bytes:
            raise LimitError("Manifest exceeds policy")
        if info.compress_type != 0 or info.compress_size != info.file_size:
            raise FormatError("Only uncompressed STORE members are permitted")
        if info.flag_bits not in (8, 0x808) or info.volume or info.comment:
            raise FormatError("Unsupported ZIP flags or metadata")
        if (
            info.create_system != 3
            or info.external_attr != (0o100600 << 16)
            or info.date_time != (1980, 1, 1, 0, 0, 0)
        ):
            raise FormatError("Non-canonical ZIP member attributes")
        if info.header_offset != position:
            raise FormatError("Overlapping, gapped or reordered ZIP members")
        _extra(info.extra)
        total += info.file_size
        if total > limits.max_total_bytes + limits.max_manifest_bytes:
            raise LimitError("Archive payload exceeds policy")
        stream.seek(position)
        local = struct.unpack("<4s5H3L2H", read_exact(stream, 30))
        sig, version, flags, method, time, date, crc, compressed, size, name_len, extra_len = local
        if (
            sig != b"PK\x03\x04"
            or version != 45
            or flags != info.flag_bits
            or method
            or time != 0
            or date != 33
            or crc != 0
            or compressed != 0xFFFFFFFF
            or size != 0xFFFFFFFF
        ):
            raise FormatError("Non-canonical local ZIP header")
        if name_len > 1024 or extra_len != 20:
            raise FormatError("Invalid ZIP local lengths")
        name = read_exact(stream, name_len)
        encoding = "utf-8" if flags & 0x800 else "ascii"
        try:
            if name.decode(encoding) != info.filename:
                raise FormatError("ZIP filename mismatch")
        except UnicodeError as exc:
            raise FormatError("Invalid filename encoding") from exc
        if read_exact(stream, 20) != struct.pack("<HHQQ", 1, 16, 0, 0):
            raise FormatError("Non-canonical local ZIP64 extra")
        descriptor_at = position + 30 + name_len + 20 + info.file_size
        if descriptor_at + 24 > cd_offset:
            raise FormatError("Member exceeds data region")
        stream.seek(descriptor_at)
        sig, crc, compressed, size = struct.unpack("<4sLQQ", read_exact(stream, 24))
        if (
            sig != b"PK\x07\x08"
            or crc != info.CRC
            or compressed != info.file_size
            or size != info.file_size
        ):
            raise FormatError("ZIP descriptor mismatch")
        position = descriptor_at + 24
    if position != cd_offset or infos[-1].filename != MANIFEST:
        raise FormatError("Invalid ZIP layout or missing final manifest")
    return infos


def verify_archive(stream, *, limits=Limits(), trusted_signers=(), require_signature=False):
    count, offset = _preflight(stream, limits)
    try:
        archive = zipfile.ZipFile(stream, "r")
        infos = _layout(stream, archive, count, offset, limits)
        raw = archive.read(MANIFEST)
        manifest = parse_json(raw, limits.max_manifest_bytes)
        fields(manifest, {"format", "files"}, {"signature"})
        if manifest["format"] != MANIFEST_FORMAT or not isinstance(manifest["files"], list):
            raise FormatError("Invalid manifest")
        records = manifest["files"]
        if len(records) != len(infos) - 1:
            raise IntegrityError("Manifest does not cover every member")
        previous = None
        total = 0
        for record, info in zip(records, infos[:-1], strict=True):
            fields(record, {"path", "size", "sha256"})
            path = portable_path(record["path"])
            if previous is not None and path <= previous:
                raise FormatError("Manifest paths must be strictly sorted")
            previous = path
            if (
                path != info.filename
                or type(record["size"]) is not int
                or record["size"] != info.file_size
            ):
                raise IntegrityError("Manifest/member mismatch")
            expected = record["sha256"]
            if (
                not isinstance(expected, str)
                or len(expected) != 64
                or any(c not in "0123456789abcdef" for c in expected)
            ):
                raise FormatError("Invalid member digest")
            hasher = hashlib.sha256()
            with archive.open(info) as source:
                while data := source.read(CHUNK):
                    hasher.update(data)
            if hasher.hexdigest() != expected:
                raise IntegrityError("Member digest mismatch")
            total += info.file_size
        if total > limits.max_total_bytes:
            raise LimitError("Total content exceeds policy")
        signer_id = None
        trusted = False
        if "signature" in manifest:
            signature = manifest["signature"]
            fields(signature, {"algorithm", "public_key", "value"})
            if signature["algorithm"] != "ed25519":
                raise FormatError("Unsupported signature algorithm")
            public = unb64(signature["public_key"], 32)
            unsigned = {k: v for k, v in manifest.items() if k != "signature"}
            try:
                VerifyKey(public).verify(
                    SIGN_DOMAIN + canonical(unsigned), unb64(signature["value"], 64)
                )
            except BadSignatureError as exc:
                raise IntegrityError("Invalid manifest signature") from exc
            signer_id = hashlib.sha256(public).hexdigest()
            trusted = public in trusted_signers
        if (require_signature or trusted_signers) and not trusted:
            raise PolicyError("A signature from an explicitly trusted key is required")
        report = {
            "format": "kristal.container-verification/1",
            "integrity": "verified",
            "file_count": len(records),
            "total_bytes": total,
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "signature": "trusted" if trusted else "valid-untrusted" if signer_id else "absent",
            "signer_id": signer_id,
            "semantic_validation": "not-performed",
        }
        return archive, manifest, report
    except (zipfile.BadZipFile, EOFError, UnicodeError, struct.error, NotImplementedError) as exc:
        raise FormatError("Invalid ZIP structure or CRC") from exc
