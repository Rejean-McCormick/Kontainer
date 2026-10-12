"""Kristal Container. Physical representation is not logical identity."""

from .api import Container, inspect_header, pack
from .common import Limits
from .crypto import Credentials, Protection
from .errors import (
    AccessError,
    ContainerError,
    FormatError,
    IntegrityError,
    LimitError,
    PolicyError,
    UnsupportedError,
)

__version__ = "1.0.0rc1"
__all__ = [
    "Container",
    "Credentials",
    "Protection",
    "Limits",
    "pack",
    "inspect_header",
    "ContainerError",
    "FormatError",
    "IntegrityError",
    "AccessError",
    "PolicyError",
    "LimitError",
    "UnsupportedError",
]
