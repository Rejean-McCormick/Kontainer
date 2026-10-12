import io
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from kristal_container import Container, ContainerError
from kristal_container.common import Limits, canonical, parse_json
from kristal_container.crypto import _hkdf, read_header
from kristal_container.staging import EncryptedSpool


@given(st.binary(max_size=4096))
@settings(max_examples=150, deadline=None)
def test_arbitrary_inputs_are_bounded(data):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "input"
        path.write_bytes(data)
        with pytest.raises(ContainerError):
            Container(path, limits=Limits(max_total_bytes=4096, max_files=8))


@given(st.binary(max_size=4096))
@settings(max_examples=100, deadline=None)
def test_encrypted_spool_read_seek(data):
    with EncryptedSpool(4097) as spool:
        for start in range(0, len(data), 97):
            spool.write(data[start : start + 97])
        spool.seal()
        assert spool.read() == data
        for start in range(0, len(data), 101):
            spool.seek(start)
            assert spool.read(107) == data[start : start + 107]
        spool.seek(10000)
        assert spool.read(10) == b""


@given(
    st.dictionaries(
        st.text(alphabet="abcdef", max_size=10), st.integers(-100000, 100000), max_size=15
    )
)
def test_canonical_serialization_is_stable(value):
    raw = canonical(value)
    assert canonical(parse_json(raw, 4096)) == raw


def test_hkdf_rfc5869_known_answer():
    # RFC 5869 test case 1: first 32 output bytes.
    ikm = bytes.fromhex("0b" * 22)
    salt = bytes.fromhex("000102030405060708090a0b0c")
    info = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9")
    assert (
        _hkdf(ikm, salt, info).hex()
        == "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
    )


def test_header_length_bomb():
    with pytest.raises(ContainerError):
        read_header(io.BytesIO(b"KRISTAL\x01\xff\xff\xff\xff"))
