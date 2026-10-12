import pytest


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "state").mkdir()
    (root / "state" / "snapshot.json").write_bytes(b'{"logical_commitment":"unchanged-example"}\n')
    (root / "notes.txt").write_text("Bonjour Kristal — données privées", encoding="utf-8")
    (root / "empty.bin").write_bytes(b"")
    return root
