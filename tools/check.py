"""Run local quality gates; no installation, network, publication or activation."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for command in (
    [sys.executable, "-m", "ruff", "check", "src", "tests", "tools"],
    [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "tools"],
    [sys.executable, "-m", "pytest", "-q"],
):
    subprocess.run(command, cwd=root, check=True)
