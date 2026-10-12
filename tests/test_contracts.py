import json
import struct
from pathlib import Path

import jsonschema

from kristal_container import Container, Credentials, Protection, pack
from kristal_container.crypto import KDF, make_header

ROOT = Path(__file__).resolve().parents[1]


def schema(name):
    return json.loads((ROOT / "contracts" / f"{name}.schema.json").read_text())


def test_generated_headers_and_manifest_match_schemas(source, tmp_path):
    header_schema, manifest_schema = schema("header"), schema("manifest")
    for protection in (Protection(), Protection(password="phrase secrète pour schéma")):
        path = tmp_path / ("encrypted" if protection.encrypted else "open")
        pack(source, path, protection=protection)
        raw = path.read_bytes()
        length = struct.unpack(">I", raw[8:12])[0]
        jsonschema.validate(json.loads(raw[12 : 12 + length]), header_schema)
        with Container(path, credentials=Credentials(password=protection.password)) as c:
            jsonschema.validate(c._manifest, manifest_schema)


def test_fixed_kdf_in_schema():
    header, _ = make_header(Protection(password="phrase secrète pour schéma"))
    assert header["slots"][0]["kdf"] == KDF
    header["slots"][0]["kdf"] = {**KDF, "iterations": 1}
    validator = jsonschema.Draft202012Validator(schema("header"))
    assert not validator.is_valid(header)


def test_open_conformance_vector():
    vector = ROOT / "examples" / "open-v1.kristal"
    expected = json.loads((ROOT / "examples" / "open-v1.expected.json").read_text())
    with Container(vector, expected_sha256=expected["container_sha256"]) as c:
        assert c.report == expected
