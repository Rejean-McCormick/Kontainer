# Qualification and release

## Delivery checks

1. Isolated environment, runtime constraints, tests and lint.
2. Wheel + sdist build; install wheel and exercise CLI with synthetic data.
3. Schema/vector verification and absence of real secrets in the archive.
4. Dated VALIDATION report distinguishing observed results from steps not executed.
5. Source archive and SHA-256 hashes. A hash shipped with the package is not a distribution signature from a trusted identity.

## Before sensitive production

- Independent cryptographic review of the envelope and access-method composition.
- CI actually run across supported Python/OS versions, especially Windows/NTFS and ACLs.
- Large-volume/ZIP64 tests on target storage, process interruption and disk exhaustion.
- Dependency/CVE review at release time; platform-appropriate hash-locked dependencies and a complete SBOM for binary distribution.
- Explicit Framework adoption of the contract and independent interoperability tests.
- Recovery exercise with actual custodians and fallback procedures.
- Provider-specific qualification under PROVIDERS.md for hardware/managed providers.
- Owner-selected license and private security reporting channel before public distribution.

CI workflows do not publish any package or production file. GitHub repository creation, pushes, releases and activation are separate operations.

## Versions and migration

The release candidate freezes a proposed v1 format for review. Incompatible changes before adoption must be declared and accompanied by an explicit, verified conversion tool. A migration must never silently replace existing files or lose recovery mechanisms.

## Rollback

By default the engine writes new files and leaves sources unchanged. Roll back to the previous software version and earlier validated copies. After explicit `--overwrite`, restoration depends on the owner's backup: atomicity is not version history.
