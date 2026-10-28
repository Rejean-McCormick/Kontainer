# Contracts

JSON Schema 2020-12 schemas support interoperability and tests. The runtime parser enforces additional essential checks: exact canonicalization, decoded Base64 length, unique slots, KDF parameters, portable filenames, size consistency, signature verification, and stream authentication.

Schema validation alone is never sufficient to accept a file. The manifest schema describes default ceilings; integrations that adjust `Limits` must adapt their own checks. The complete normative contract is `docs/FORMAT.md`, proposed to the Framework.
