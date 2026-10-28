# Delivery report

## Repository

New standalone `Kristal-Container` repository, version 1.0.0rc1. Includes a Python library, CLI, English-language documentation (translated in this edition), schemas, tests, verification tools, CI, conformance vectors and installable package.

## Files and responsibilities

- `src/kristal_container/`: engine implementation, keys, parser, storage, and API.
- `tests/`: functional, adversarial and generative tests; Local Kit contract and providers.
- `contracts/` and `docs/FORMAT.md`: contract proposal for adoption by Framework.
- `docs/`: usage, API, architecture, recovery, threats, providers, decisions, references and evidence.
- `.github/`: multi-platform tests and proposed dependency updates, without publication.
- `examples/`: only synthetic data and a verifiable open container.
- `tools/`: local gates and opt-in benchmark.

No source archive file is modified by the original software delivery. No canonical workspace, external repository, account, server or device is activated or configured.

## New contracts

`kristal.container/1`, `kristal.container-manifest/1`, `kristal.key/1`, verification/capability reports and Python provider interfaces. The only existing contract consumed is the `kristal.github-read-surface/1.0` projection. No semantic contract is redefined.

## Rollback

Normal creation writes a new file and leaves the source folder intact. The software package can be removed from its virtual environment. An explicitly requested overwrite requires a previous backup to recover that version. Removing the software does not delete secrets/files kept by the owner.

## Integrate separately

Framework adoption of the contract; Authoring Kit export commands; Manager dialogs; Kompiler/Konstellation reader APIs; hardware/organizational providers for the chosen deployment profile. None of these cross-repository changes is claimed to have been installed.
