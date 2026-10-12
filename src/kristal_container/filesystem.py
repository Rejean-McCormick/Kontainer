"""Filesystem boundaries. Callers must own/trust source and destination parents."""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from pathlib import Path

from .errors import PolicyError


def reject_links(path: Path):
    path = Path(os.path.abspath(path))
    for component in (*reversed(path.parents), path):
        if component.exists() or component.is_symlink():
            info = component.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise PolicyError("Symlinks and Windows reparse points are forbidden")
    return path


@contextlib.contextmanager
def regular_input(path: Path):
    path = reject_links(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise PolicyError("Input must be a regular file")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino) != (
            opened.st_dev,
            opened.st_ino,
        ):
            raise PolicyError("Input changed while opening")
        yield stream


def sync_directory(path: Path):
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


@contextlib.contextmanager
def atomic_output(path: Path, *, overwrite=False):
    path = reject_links(path)
    if not path.parent.is_dir():
        raise PolicyError("Destination parent must already exist")
    if path.exists() and not overwrite:
        raise PolicyError("Destination already exists")
    fd, temporary = tempfile.mkstemp(prefix=".kristal-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as output:
            yield output
            output.flush()
            os.fsync(output.fileno())
        reject_links(path)
        if overwrite:
            if path.exists() and not path.is_file():
                raise PolicyError("Destination is not a file")
            os.replace(temporary, path)
        else:
            # Hardlink publication is atomic and fails if destination appeared.
            # No racy exists()+rename() fallback on filesystems without hardlinks.
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                raise PolicyError("Destination already exists") from exc
            temporary.unlink()
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)
