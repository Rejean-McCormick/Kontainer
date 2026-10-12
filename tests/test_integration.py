import hashlib
import hmac
import json
import os

import pytest
from nacl.public import PrivateKey, SealedBox

from kristal_container import Container, Credentials, Protection, pack
from kristal_container.cli import main
from kristal_container.errors import AccessError, IntegrityError, PolicyError
from kristal_container.integration import pack_read_surface


def projection(source):
    data = (source / "notes.txt").read_bytes()
    return {
        "format": "kristal.github-read-surface/1.0",
        "ready": True,
        "errors": [],
        "file_count": 1,
        "total_bytes": len(data),
        "files": [
            {
                "path": "notes.txt",
                "size": len(data),
                "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            }
        ],
    }


def test_read_surface_exact_bytes(source, tmp_path):
    supplied = projection(source)
    pack_read_surface(source, tmp_path / "surface", supplied)
    with Container(tmp_path / "surface") as c:
        assert [x["path"] for x in c.list()] == ["notes.txt"]
    (source / "notes.txt").write_text("changed")
    with pytest.raises(IntegrityError):
        pack_read_surface(source, tmp_path / "stale", supplied)
    assert not (tmp_path / "stale").exists()


def test_read_surface_requires_ready(source, tmp_path):
    supplied = projection(source)
    supplied["ready"] = False
    with pytest.raises(PolicyError):
        pack_read_surface(source, tmp_path / "surface", supplied)


def test_factor_provider_requires_secret_and_password(source, tmp_path):
    class TestFactor:
        # Test double only; not a hardware authenticator.
        def __init__(self):
            self.key = os.urandom(32)
            self.calls = []

        def derive(self, cid):
            self.calls.append(cid)
            return hmac.digest(self.key, cid, "sha256")

    factor = TestFactor()
    password = "Un secret pour le test matériel"
    path = tmp_path / "a"
    pack(source, path, protection=Protection(password=password, factor_provider=factor))
    with pytest.raises(AccessError):
        Container(path, credentials=Credentials(password=password))
    with Container(path, credentials=Credentials(password=password, factor_provider=factor)):
        pass
    assert factor.calls[0] == factor.calls[1]
    assert len(factor.calls[0]) == 16


def test_recipient_resolver_is_explicitly_allowlisted(source, tmp_path):
    identity = PrivateKey.generate()
    key_id = hashlib.sha256(bytes(identity.public_key)).hexdigest()

    class TestResolver:
        calls = 0

        def unwrap(self, *, key_id, container_id, wrapped, header_sha256):
            self.calls += 1
            assert len(header_sha256) == 32
            return SealedBox(identity).decrypt(wrapped)

    resolver = TestResolver()
    path = tmp_path / "a"
    pack(source, path, protection=Protection(recipients=(bytes(identity.public_key),)))
    with pytest.raises(AccessError):
        Container(path, credentials=Credentials(recipient_resolver=resolver))
    assert resolver.calls == 0
    with Container(
        path, credentials=Credentials(recipient_resolver=resolver, allowed_recipient_ids=(key_id,))
    ):
        pass
    assert resolver.calls == 1


def test_cli_open_plan_pack_verify_export(source, tmp_path, capsys):
    assert main(["plan", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["written"] is False
    path = tmp_path / "a"
    assert main(["pack", str(source), str(path), "--mode", "open"]) == 0
    capsys.readouterr()
    assert main(["verify", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["integrity"] == "verified"
    dest = tmp_path / "notes"
    assert main(["export", str(path), "notes.txt", str(dest), "--allow-plaintext"]) == 0
    assert dest.read_bytes() == (source / "notes.txt").read_bytes()


def test_cli_password_fd_does_not_print_secret(source, tmp_path, capsys):
    secret = tmp_path / "secret"
    secret.write_text("Phrase longue pour vérifier la CLI\n", encoding="utf-8")
    path = tmp_path / "a"
    with secret.open("rb") as f:
        assert (
            main(
                [
                    "pack",
                    str(source),
                    str(path),
                    "--mode",
                    "password",
                    "--password-fd",
                    str(f.fileno()),
                ]
            )
            == 0
        )
    with secret.open("rb") as f:
        assert main(["verify", str(path), "--password-fd", str(f.fileno())]) == 0
    captured = capsys.readouterr()
    assert "Phrase longue" not in captured.out + captured.err


def test_cli_keygen_and_wrong_type(tmp_path, capsys):
    key = tmp_path / "recovery.ksecret"
    assert main(["keygen", "recovery", str(key)]) == 0
    assert json.loads(capsys.readouterr().out)["secret_printed"] is False
    assert main(["keygen", "recovery", str(key)]) == 2
    assert json.loads(capsys.readouterr().err)["error"] == "policy-denied"
