"""Append-only encrypted temporary storage with a seekable read view.

No plaintext spill to disk. Keys and decrypted blocks remain in process memory;
this does not protect against swap, a debugger, malware or an administrator.
"""

from __future__ import annotations

import io
import os
import struct
import tempfile

from nacl.bindings import crypto_aead_xchacha20poly1305_ietf_decrypt as decrypt
from nacl.bindings import crypto_aead_xchacha20poly1305_ietf_encrypt as encrypt
from nacl.exceptions import CryptoError

from .common import CHUNK
from .errors import IntegrityError, LimitError


class EncryptedSpool(io.RawIOBase):
    def __init__(self, maximum: int):
        super().__init__()
        self._file = tempfile.TemporaryFile("w+b")
        self._key = os.urandom(32)
        self._nonce = os.urandom(16)
        self._buffer = bytearray()
        self._maximum = maximum
        self._size = 0
        self._position = 0
        self._blocks = 0
        self._sealed = False
        self._cached_index = -1
        self._cached = b""

    def writable(self):
        return not self._sealed

    def readable(self):
        return self._sealed

    def seekable(self):
        return self._sealed

    def tell(self):
        return self._position if self._sealed else self._size

    def write(self, data):
        self._checkClosed()
        if self._sealed:
            raise io.UnsupportedOperation("sealed spool")
        if self._size + len(data) > self._maximum:
            raise LimitError("Staging limit exceeded")
        self._size += len(data)
        view = memoryview(data)
        while view:
            n = min(CHUNK - len(self._buffer), len(view))
            self._buffer.extend(view[:n])
            view = view[n:]
            if len(self._buffer) == CHUNK:
                self._flush_block()
        return len(data)

    def _flush_block(self):
        if not self._buffer:
            return
        index = struct.pack(">Q", self._blocks)
        self._file.write(
            encrypt(
                bytes(self._buffer), b"kristal-stage-v1" + index, self._nonce + index, self._key
            )
        )
        self._blocks += 1
        self._buffer.clear()

    def seal(self):
        if not self._sealed:
            self._flush_block()
            self._file.flush()
            self._sealed = True
            self._position = 0
        return self

    def seek(self, offset, whence=io.SEEK_SET):
        self._checkClosed()
        if not self._sealed:
            raise io.UnsupportedOperation("append-only spool")
        if whence not in (0, 1, 2):
            raise ValueError("invalid seek mode")
        position = offset + (0 if whence == 0 else self._position if whence == 1 else self._size)
        if position < 0:
            raise ValueError("negative seek")
        self._position = position
        return position

    def read(self, size=-1):
        self._checkClosed()
        if not self._sealed:
            raise io.UnsupportedOperation("unsealed spool")
        remaining = max(0, self._size - self._position)
        size = remaining if size is None or size < 0 else min(size, remaining)
        out = bytearray()
        while len(out) < size:
            index, start = divmod(self._position, CHUNK)
            if self._cached_index != index:
                self._file.seek(index * (CHUNK + 16))
                length = min(CHUNK, self._size - index * CHUNK)
                cipher = self._file.read(length + 16)
                packed = struct.pack(">Q", index)
                try:
                    self._cached = decrypt(
                        cipher, b"kristal-stage-v1" + packed, self._nonce + packed, self._key
                    )
                except CryptoError as exc:
                    raise IntegrityError("Encrypted temporary storage changed") from exc
                self._cached_index = index
            n = min(size - len(out), len(self._cached) - start)
            out.extend(self._cached[start : start + n])
            self._position += n
        return bytes(out)

    def close(self):
        if not self.closed:
            self._file.close()
            self._buffer.clear()
            self._cached = b""
            self._key = b""
        super().close()
