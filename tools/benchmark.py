"""Opt-in local synthetic benchmark. Writes only inside an ephemeral directory."""

import argparse
import json
import os
import platform
import tempfile
import time
from pathlib import Path

from kristal_container import Container, Credentials, Protection, pack

parser = argparse.ArgumentParser()
parser.add_argument("--mib", type=int, default=64)
args = parser.parse_args()
if not 1 <= args.mib <= 1024:
    parser.error("--mib must be in 1..1024")
with tempfile.TemporaryDirectory(prefix="kristal-benchmark-") as directory:
    root = Path(directory)
    source = root / "source"
    source.mkdir()
    with (source / "synthetic.bin").open("wb") as output:
        for _ in range(args.mib):
            output.write(os.urandom(1024**2))
    password = os.urandom(32).hex()
    start = time.perf_counter()
    pack(source, root / "test.kristal", protection=Protection(password=password))
    packed = time.perf_counter()
    with Container(root / "test.kristal", credentials=Credentials(password=password)) as reader:
        report = reader.report
    verified = time.perf_counter()
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.system(),
                "payload_bytes": report["total_bytes"],
                "container_bytes": (root / "test.kristal").stat().st_size,
                "pack_seconds": round(packed - start, 4),
                "verify_seconds": round(verified - packed, 4),
                "note": "Synthetic local measurement; not a cross-platform performance guarantee.",
            },
            indent=2,
        )
    )
