import io
import os

import pytest
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from kristal_container import (
    AccessError,
    Container,
    Credentials,
    IntegrityError,
    Limits,
    PolicyError,
    Protection,
    inspect_header,
    pack,
)
from kristal_container.errors import LimitError
from kristal_container.keys import generate_key, load_key, save_key

PASSWORD = "Un long secret indépendant 2026!"


def test_open_roundtrip_and_determinism(source, tmp_path):
    a, b = tmp_path / "a.kristal", tmp_path / "b.kristal"
    pack(source, a)
    pack(source, b)
    assert a.read_bytes() == b.read_bytes()
    assert inspect_header(a) == {
        "format": "kristal.container/1",
        "mode": "open",
        "verified": False,
        "access_methods": [],
    }
    with Container(a) as reader:
        assert reader.report["semantic_validation"] == "not-performed"
        assert reader.report["signature"] == "absent"
        for entry in reader.list():
            assert reader.read(entry["path"]) == (source / entry["path"]).read_bytes()
        reader.extract(tmp_path / "restored")
        with pytest.raises(PolicyError):
            reader.extract(tmp_path / "restored")
    assert (tmp_path / "restored/notes.txt").read_bytes() == (source / "notes.txt").read_bytes()


def test_password_confidentiality_and_randomization(source, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    pack(source, a, protection=Protection(password=PASSWORD))
    pack(source, b, protection=Protection(password=PASSWORD))
    assert a.read_bytes() != b.read_bytes()
    assert b"snapshot.json" not in a.read_bytes()
    assert b"logical_commitment" not in a.read_bytes()
    for credentials in (Credentials(), Credentials(password="wrong")):
        with pytest.raises(AccessError):
            Container(a, credentials=credentials)
    with Container(a, credentials=Credentials(password=PASSWORD), require_encrypted=True) as reader:
        assert reader.read("notes.txt") == (source / "notes.txt").read_bytes()


def test_two_secrets_are_and_recovery_is_or(source, tmp_path):
    factor, recovery = os.urandom(32), os.urandom(32)
    path = tmp_path / "protected"
    pack(source, path, protection=Protection(password=PASSWORD, factor=factor, recovery=recovery))
    for c in (
        Credentials(password=PASSWORD),
        Credentials(factor=factor),
        Credentials(password=PASSWORD, factor=os.urandom(32)),
        Credentials(recovery=os.urandom(32)),
    ):
        with pytest.raises(AccessError):
            Container(path, credentials=c)
    for c in (Credentials(password=PASSWORD, factor=factor), Credentials(recovery=recovery)):
        with Container(path, credentials=c) as reader:
            assert reader.report["integrity"] == "verified"


def test_recipient_and_recovery(source, tmp_path):
    first, second, stranger = (PrivateKey.generate() for _ in range(3))
    recovery = os.urandom(32)
    path = tmp_path / "shared"
    pack(
        source,
        path,
        protection=Protection(
            recipients=(bytes(first.public_key), bytes(second.public_key)), recovery=recovery
        ),
    )
    for c in (
        Credentials(identity=bytes(first)),
        Credentials(identity=bytes(second)),
        Credentials(recovery=recovery),
    ):
        with Container(path, credentials=c) as reader:
            assert reader.read("empty.bin") == b""
    with pytest.raises(AccessError):
        Container(path, credentials=Credentials(identity=bytes(stranger)))


def test_signature_requires_external_trust(source, tmp_path):
    signer, stranger = SigningKey.generate(), SigningKey.generate()
    path = tmp_path / "signed"
    pack(source, path, signing_key=bytes(signer))
    with Container(path) as reader:
        assert reader.report["signature"] == "valid-untrusted"
    for trusted in ((), (bytes(stranger.verify_key),)):
        with pytest.raises(PolicyError):
            Container(path, require_signature=True, trusted_signers=trusted)
    with Container(path, trusted_signers=(bytes(signer.verify_key),)) as reader:
        assert reader.report["signature"] == "trusted"


def test_rewrap_preserves_archive_and_signature(source, tmp_path):
    signer = SigningKey.generate()
    first, second = tmp_path / "first", tmp_path / "second"
    recovery = os.urandom(32)
    pack(source, first, signing_key=bytes(signer), protection=Protection(password=PASSWORD))
    with Container(first, credentials=Credentials(password=PASSWORD)) as reader:
        manifest_digest = reader.report["manifest_sha256"]
        reader.rewrap(second, protection=Protection(recovery=recovery))
        with pytest.raises(PolicyError):
            reader.rewrap(tmp_path / "plain", protection=Protection())
        reader.rewrap(tmp_path / "plain", protection=Protection(), allow_plaintext=True)
    with pytest.raises(AccessError):
        Container(second, credentials=Credentials(password=PASSWORD))
    with Container(
        second,
        credentials=Credentials(recovery=recovery),
        trusted_signers=(bytes(signer.verify_key),),
    ) as reader:
        assert reader.report["manifest_sha256"] == manifest_digest
        assert reader.report["signature"] == "trusted"
    # Rotation must not pretend that previously distributed files are revoked.
    with Container(first, credentials=Credentials(password=PASSWORD)):
        pass


def test_expected_digest_and_encryption_policy(source, tmp_path):
    path = tmp_path / "a"
    pack(source, path)
    with Container(path) as c:
        digest = c.report["container_sha256"]
    with Container(path, expected_sha256=digest):
        pass
    with pytest.raises(IntegrityError):
        Container(path, expected_sha256="0" * 64)
    with pytest.raises(PolicyError):
        Container(path, require_encrypted=True)


def test_streaming_across_multiple_blocks(source, tmp_path):
    content = os.urandom(3 * 1024 * 1024 + 13)
    (source / "big.bin").write_bytes(content)
    path = tmp_path / "a"
    pack(source, path, protection=Protection(password=PASSWORD))
    with Container(
        path, credentials=Credentials(password=PASSWORD), limits=Limits(max_read_bytes=1024)
    ) as c:
        with pytest.raises(LimitError):
            c.read("big.bin")
        output = io.BytesIO()
        c.copy_to("big.bin", output)
        assert output.getvalue() == content


@pytest.mark.parametrize("kind", ["identity", "signing", "factor", "recovery"])
def test_typed_key_files(tmp_path, kind):
    private, public = generate_key(kind)
    file = tmp_path / "key"
    password = PASSWORD if public else None
    save_key(file, kind, private, password=password)
    assert load_key(file, kind, password=password) == private
    if public:
        assert private not in file.read_bytes()
        with pytest.raises(AccessError):
            load_key(file, kind, password="bad")
    with pytest.raises(Exception) as caught:
        load_key(file, "verify", password=password)
    assert caught.value.code == "invalid-format"


def test_empty_tree(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    pack(root, tmp_path / "a")
    with Container(tmp_path / "a") as c:
        assert c.list() == []
