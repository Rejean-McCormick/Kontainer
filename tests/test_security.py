import io
import json
import os
import struct
import zipfile

import pytest
from nacl.signing import SigningKey

from kristal_container import Container, ContainerError, Credentials, Limits, Protection, pack
from kristal_container.archive import MANIFEST_FORMAT, _zip_info
from kristal_container.common import FORMAT, MAGIC, MANIFEST, PathSet, canonical, portable_path
from kristal_container.crypto import read_header
from kristal_container.errors import (
    FormatError,
    IntegrityError,
    LimitError,
    PolicyError,
    UnsupportedError,
)
from kristal_container.staging import EncryptedSpool

PASSWORD = "Une phrase secrète très longue!"


def split(raw):
    n = struct.unpack(">I", raw[8:12])[0]
    return json.loads(raw[12 : 12 + n]), raw[12 + n :]


def join(header, payload):
    raw = canonical(header)
    return MAGIC + struct.pack(">I", len(raw)) + raw + payload


def archive_bytes(entries, manifest=None):
    with EncryptedSpool(1024 * 1024) as spool:
        with zipfile.ZipFile(spool, "w") as z:
            for name, value in entries:
                with z.open(_zip_info(name), "w", force_zip64=True) as f:
                    f.write(value)
            if manifest is not None:
                with z.open(_zip_info(MANIFEST), "w", force_zip64=True) as f:
                    f.write(canonical(manifest))
        spool.seal()
        return spool.read()


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "a/../b",
        "C:/file",
        "a\\b",
        "a//b",
        "a/",
        "a:stream",
        "NUL",
        "COM1.txt",
        "LPT¹",
        "a. ",
        "a\x00b",
        "a\u202eb",
        "e\u0301.txt",
        "_kristal/private",
    ],
)
def test_unsafe_names(name):
    with pytest.raises(FormatError):
        portable_path(name)


@pytest.mark.parametrize(
    "names", [("a", "a/b"), ("a/b", "a"), ("A/x", "a/y"), ("a", "A"), ("a", "a")]
)
def test_aliases(names):
    seen = PathSet()
    seen.add(names[0])
    with pytest.raises(FormatError):
        seen.add(names[1])


def test_source_symlink_sensitive_and_selection(source, tmp_path):
    (source / ".env").write_text("API_KEY=secret")
    with pytest.raises(PolicyError):
        pack(source, tmp_path / "a")
    assert not (tmp_path / "a").exists()
    pack(source, tmp_path / "a", selected=("notes.txt",))
    with Container(tmp_path / "a") as c:
        assert [f["path"] for f in c.list()] == ["notes.txt"]
    try:
        (source / "link").symlink_to(tmp_path / "a")
    except OSError:
        pytest.skip("OS does not permit symlink creation")
    with pytest.raises(PolicyError):
        pack(source, tmp_path / "b", selected=("link",))


def test_no_output_inside_source_no_overwrite(source, tmp_path):
    with pytest.raises(PolicyError):
        pack(source, source / "file.kristal")
    file = tmp_path / "existing"
    file.write_bytes(b"preserve")
    with pytest.raises(PolicyError):
        pack(source, file)
    assert file.read_bytes() == b"preserve"


def test_transaction_failure_preserves_previous_output(source, tmp_path, monkeypatch):
    import kristal_container.api as api

    path = tmp_path / "a"
    path.write_bytes(b"old")

    def fail(archive, output, protection):
        output.write(b"partial")
        raise RuntimeError("simulated interruption")

    monkeypatch.setattr(api, "write_envelope", fail)
    with pytest.raises(RuntimeError):
        pack(source, path, overwrite=True)
    assert path.read_bytes() == b"old"
    assert not list(tmp_path.glob(".kristal-*.tmp"))


def test_limits_before_writing(source, tmp_path):
    with pytest.raises(LimitError):
        pack(source, tmp_path / "a", limits=Limits(max_files=1))
    with pytest.raises(LimitError):
        pack(source, tmp_path / "a", limits=Limits(max_file_bytes=1))
    assert not (tmp_path / "a").exists()


def test_header_kdf_rejected_before_evaluation(source, tmp_path, monkeypatch):
    import kristal_container.crypto as crypto

    path = tmp_path / "a"
    pack(source, path, protection=Protection(password=PASSWORD))
    header, payload = split(path.read_bytes())
    header["slots"][0]["kdf"]["memory_kib"] = 2**60
    path.write_bytes(join(header, payload))

    def forbidden(*args, **kwargs):
        pytest.fail("Untrusted KDF executed")

    monkeypatch.setattr(crypto, "_password_key", forbidden)
    with pytest.raises(UnsupportedError):
        Container(path, credentials=Credentials(password=PASSWORD))


def test_unknown_profile_and_duplicate_json():
    for obj in (
        {"format": "kristal.container/99", "mode": "open"},
        {"format": FORMAT, "mode": "tpm"},
    ):
        with pytest.raises(ContainerError):
            read_header(io.BytesIO(join(obj, b"")))
    raw = b'{"format":"kristal.container/1","mode":"open","mode":"open"}'
    with pytest.raises(FormatError):
        read_header(io.BytesIO(MAGIC + struct.pack(">I", len(raw)) + raw))


def test_header_bound_to_ciphertext(source, tmp_path):
    path = tmp_path / "a"
    recovery = os.urandom(32)
    pack(source, path, protection=Protection(password=PASSWORD, recovery=recovery))
    header, payload = split(path.read_bytes())
    header["slots"].pop()  # Password key slot still opens, but payload authenticates all slots.
    path.write_bytes(join(header, payload))
    with pytest.raises(IntegrityError):
        Container(path, credentials=Credentials(password=PASSWORD))


def test_encrypted_tamper_truncate_append_and_reorder(source, tmp_path):
    (source / "big").write_bytes(b"x" * (2 * 1024**2))
    path = tmp_path / "a"
    recovery = os.urandom(32)
    pack(source, path, protection=Protection(recovery=recovery))
    original = path.read_bytes()
    header, payload = split(original)
    n = struct.unpack(">I", payload[:4])[0] + 4
    m = struct.unpack(">I", payload[n : n + 4])[0] + 4
    altered = bytearray(payload)
    altered[100] ^= 1
    candidates = [
        original[:-1],
        original[:-21],
        original + b"x",
        join(header, bytes(altered)),
        join(header, payload[n : n + m] + payload[:n] + payload[n + m :]),
        join(header, payload[:n] + payload[:n] + payload[n:]),
    ]
    for raw in candidates:
        path.write_bytes(raw)
        with pytest.raises(ContainerError):
            Container(path, credentials=Credentials(recovery=recovery))


def test_plaintext_archive_attacks(tmp_path):
    path = tmp_path / "a"
    manifest = {"format": MANIFEST_FORMAT, "files": []}
    candidates = [
        archive_bytes([("../escape", b"x")], manifest),
        archive_bytes([("undeclared", b"x")], manifest),
        archive_bytes([], manifest) + b"trailing",
    ]
    # Foreign ZIP compression and permissive ZIP attributes are not accepted.
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as f:
        f.writestr(MANIFEST, canonical(manifest))
    candidates.append(z.getvalue())
    for raw in candidates:
        path.write_bytes(join({"format": FORMAT, "mode": "open"}, raw))
        with pytest.raises(ContainerError):
            Container(path)
    assert not (tmp_path / "escape").exists()


def test_forged_manifest_signature(tmp_path):
    signer = SigningKey.generate()
    manifest = {
        "format": MANIFEST_FORMAT,
        "files": [],
        "signature": {
            "algorithm": "ed25519",
            "public_key": __import__("base64").b64encode(bytes(signer.verify_key)).decode(),
            "value": __import__("base64").b64encode(b"x" * 64).decode(),
        },
    }
    path = tmp_path / "a"
    path.write_bytes(join({"format": FORMAT, "mode": "open"}, archive_bytes([], manifest)))
    with pytest.raises(IntegrityError):
        Container(path)


def test_central_count_lie_rejected(source, tmp_path):
    path = tmp_path / "a"
    pack(source, path)
    header, payload = split(path.read_bytes())
    raw = bytearray(payload)
    struct.pack_into("<HH", raw, len(raw) - 22 + 8, 1, 1)
    path.write_bytes(join(header, bytes(raw)))
    with pytest.raises(FormatError):
        Container(path)


def test_encrypted_spool_disk_is_ciphertext():
    secret = b"do not spill plaintext" * 10000
    with EncryptedSpool(2**20) as spool:
        spool.write(secret)
        spool.seal()
        spool._file.seek(0)
        assert secret[:100] not in spool._file.read()
        spool.seek(13)
        assert spool.read(100) == secret[13:113]
        spool.seek(0)
        spool._cached_index = -1
        spool._file.seek(0)
        spool._file.write(b"tamper")
        with pytest.raises(IntegrityError):
            spool.read(10)


def test_zip64_end_records_before_32bit_sentinel(source, tmp_path, monkeypatch):
    # Python starts ZIP64 at 2 GiB, before the 4 GiB legacy sentinel. Lower
    # the threshold to exercise the exact record path without giant fixtures.
    monkeypatch.setattr(zipfile, "ZIP64_LIMIT", 64)
    path = tmp_path / "zip64"
    pack(source, path)
    assert b"PK\x06\x07" in path.read_bytes()
    with Container(path) as c:
        assert c.read("notes.txt") == (source / "notes.txt").read_bytes()
