# Release validation

Date: **October 11, 2026**. Version: **1.0.0rc1**. Actual execution platform: Linux x86-64, Python 3.12.14.

## Observed results

| Check | Result |
|---|---|
| Unit, functional and adversarial tests | **62 passed** |
| Hypothesis property-based tests | Included: bounded arbitrary inputs, spool seeks, canonicalization |
| Branch coverage measurement | **82%**, machine-readable details in VALIDATION.json |
| Runtime vulnerability-advisory search (`pip-audit 2.10.1`) | No known advisories found for the five pinned distributions |
| Ruff lint | Passed |
| Ruff format | Passed |
| Wheel and sdist build | Passed |
| Wheel installation into separate virtual environment | Passed |
| Installed-package CLI workflow | Successful open/encrypted creation, verification, recovery, rewrapping and extraction |
| JSON Schemas and pinned open vector | Passed |
| Processing of 64 MiB synthetic data | Passed; measurements in BENCHMARK.json |

Coverage is not proof of security. Numeric results come from executed local commands, not remote CI claimed to have passed.

## Threats actually tested

Missing/incorrect password; joint factor requirement; independent recovery; unauthorized recipient; unknown/forged signature; encryption policy; expected physical fingerprint; authenticated-header tampering; deleted/reordered/duplicated/truncated frames; suffixes; excessive KDF parameters rejected before derivation; duplicate JSON; absolute/traversal/ADS/Windows filenames and collisions; linked source; secrets encoded in filenames; undeclared files; unexpected compression; forged central-directory count; ZIP64 before traditional sentinel; size limits; write failure without corrupting target; encrypted temporary contents; stale Local Kit projection; allowlist before provider callback.

## Integration evidence and limitations

`pack_read_surface` is tested with a synthetic projection matching fields observed in the supplied Local Kit. This proves checks over selected bytes, not a graphical Manager workflow or recomputation of Framework State Commitments.

FactorProvider and RecipientResolver interfaces pass tests with software doubles. No physical TPM, WebAuthn user-presence, synchronized passkey, KMS or deployed Konfid test has been run. CLI reports these providers as unsupported.

The supplied CI targets Linux, Windows, macOS and Python 3.11–3.14. It was not run on GitHub for this release. ZIP64 tests lower a threshold to verify structures; an actual multi-GiB container was not qualified. The 64 MiB test is not a universal performance promise.

## Local benchmark

64 MiB of random synthetic data, no compression: approximately **0.45 s** to create and **0.35 s** to open/verify in this environment. Container size: **67,111,208 bytes** for **67,108,864 payload bytes**. Disk, CPU, OS, antivirus and manifest size affect results.

## Security status

No independent audit, certification or accreditation. This repository is a candidate implementation for integration and review; these tests alone do not justify calling it “certified” or “qualified for critical production.” See RELEASE.md for outstanding gates.

## Dependencies

`DEPENDENCY_AUDIT.json` contains the dated known-advisory search for PyNaCl, argon2-cffi, argon2-cffi-bindings, CFFI and pycparser at versions in `constraints.txt`. That search is neither a code audit nor a comprehensive review of bundled native libraries or the Python system. Development dependency versions were not included.
