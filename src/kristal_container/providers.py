"""Explicit in-process extension boundaries, never plugins named by an import.

Implementations are application-owned trusted code. A .kristal file cannot select
modules, processes, network endpoints, devices, users or approval policies.
"""

from __future__ import annotations

from typing import Protocol


class FactorProvider(Protocol):
    def derive(self, container_id: bytes) -> bytes:
        """Return 32 pseudorandom secret bytes bound to the 16-byte container ID.

        Must require whatever presence/verification policy the application claims.
        Never use a short OTP, a public signature or a system identifier as output.
        Raise on cancellation, unavailability, or failed user verification.
        The output must be reproducible for reopening the same container.
        """
        ...


class RecipientResolver(Protocol):
    def unwrap(
        self, *, key_id: str, container_id: bytes, wrapped: bytes, header_sha256: bytes
    ) -> bytes | None:
        """Return the sealed-box plaintext (container_id || 32-byte content key).

        None means no such permitted key. Authorization and user/workload binding
        are external responsibilities. Header fields remain UNAUTHENTICATED claims
        until payload validation completes, never authority to release a key.
        Must not auto-create keys or trust URLs/policies from untrusted data.
        Explicit allowlisting happens before invocation in the local caller.
        Returning a key to a client does not revoke its already acquired knowledge.
        """
        ...
