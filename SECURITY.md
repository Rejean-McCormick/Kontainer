# Security

This repository handles secrets. Read `docs/THREAT_MODEL.md`, `docs/FORMAT.md`, and `docs/VALIDATION.md` before entrusting it with sensitive production data.

## Status

Candidate implementation, locally tested, **no independent audit**. No FIPS claim, MFA/AAL certification, age compatibility, TPM qualification, or post-quantum guarantees. Unavailable capabilities are not silently enabled.

## Reporting

Do not post keys, passwords, private data, or exploit evidence containing them in a public issue. Contact the repository owner through a previously established private channel. No fictitious security contact or nonexistent address is given; the owner must configure the channel before public release.

## Changes requiring security review

- Format, signatures, key slots, KDF, AAD, nonces and framing.
- ZIP parser, paths, limits, canonicalization and memory allocation.
- Hardware/network providers, identity and authorization.
- Recovery, plaintext exports, caches, temporary files and logging.
- Cryptographic dependencies, packaging, CI and distribution.

## Invariants

Never remove a check merely to pass a test. No silent downgrades. No secrets in arguments/logs. No import or executable selected by content. No business-data bytes exposed before required verification. No existing file overwritten without an explicit option. No real secrets in fixtures or release archives.

## Maintenance

Review security advisories for Python, PyNaCl/libsodium, argon2-cffi, and their bindings. Update constraints through reviewed changes and rerun tests. A pinned dependency is not proof that vulnerabilities are absent.
