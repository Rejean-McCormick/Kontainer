# Kristal Container

**A data folder becomes a single, uncompressed, verifiable and optionally encrypted `.kristal` file.** Local Python library and CLI, with no required server or account.

Delivered version: **1.0.0rc1**. The local engine is implemented and tested; the application protocol has not received an independent cryptographic audit. The delivered contract is a proposed Framework extension, not a standard already adopted by the Framework.

## What works

| Capability | Status |
|---|---|
| Open container, inner ZIP64 STORE, portable Unicode files | Implemented |
| Passphrase, Argon2id, XChaCha20-Poly1305 `secretstream` | Implemented |
| Password **AND** external 256-bit secret | Implemented; copyable secret file, not hardware authentication |
| Multiple X25519 recipients, each with its own identity | Implemented |
| Independent recovery key | Implemented; explicitly chosen alternative access |
| Ed25519 signature and optional mandatory external trust | Implemented |
| Change protection without changing the inner bytes | Implemented |
| Encrypted temporary files, reading without extraction | Implemented |
| Local Kit `read-surface/1.0` projection adapter | Implemented |
| Python interfaces for external factor and key resolver | Implemented and tested using test doubles |
| Native TPM, WebAuthn, KMS/Konfid providers | **Not provided**; integrations must be qualified on their actual infrastructure |
| Post-quantum cryptography, cryptographic quorum, offline revocation | Unsupported; no misleading protection indicators |

`kristal-container capabilities` exposes these states as JSON. The file itself never selects a module, executable or URL to contact.

## Installation

Targets Python **3.11 through 3.14**. This release was validated locally on Linux/Python 3.12; the CI matrix provides further checks to run.

```sh
python -m venv .venv
# Linux / macOS:
.venv/bin/python -m pip install -c constraints.txt .
.venv/bin/python -m kristal_container --help
```

On Windows, from the repository directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints.txt .
.\.venv\Scripts\python.exe -m kristal_container --help
```

No permanent PATH changes, file associations, publishing, or system-wide installation. The following commands assume the virtual environment is active; otherwise use its full Python path.

## Quick start

Review selected files without writing:

```sh
python -m kristal_container plan examples/demo
```

Create an open Kristal:

```sh
python -m kristal_container pack examples/demo demo.kristal --mode open
python -m kristal_container verify demo.kristal
python -m kristal_container list demo.kristal
```

Create an encrypted Kristal; the passphrase is prompted in the terminal, never passed as an argument:

```sh
python -m kristal_container pack examples/demo prive.kristal --mode password
python -m kristal_container verify prive.kristal --password --require-encrypted
```

The header may be inspected without decryption, but its response is **unverified**:

```sh
python -m kristal_container inspect prive.kristal
```

Destinations must be outside the source directory and must not already exist, unless `--overwrite` is explicitly specified. A protected file never automatically becomes a decrypted GitHub surface.

## Recovery from the start

```sh
python -m kristal_container keygen recovery secours.ksecret
python -m kristal_container pack examples/demo protege.kristal --mode password --recovery-key secours.ksecret
python -m kristal_container verify protege.kristal --unlock-recovery secours.ksecret
```

`secours.ksecret` is a **plaintext bearer secret**: anyone who possesses it can open the file. Move it to separately protected storage and back it up independently. Never include it in the packaged folder, repository, email or software archive. Test recovery before relying on it. This repository supplies no demo secrets or passwords.

Change the password after recovery:

```sh
python -m kristal_container rewrap protege.kristal nouveau.kristal --unlock-recovery secours.ksecret --mode password --recovery-key secours.ksecret
```

The new protection replaces **all** access paths from the old envelope. Older files remain accessible using their original credentials.

## Python library

```python
from pathlib import Path
from getpass import getpass
from kristal_container import Container, Credentials, Protection, pack

phrase = getpass("Passphrase: ")
pack(Path("my-folder"), Path("my-file.kristal"),
     protection=Protection(password=phrase))
with Container(Path("my-file.kristal"),
               credentials=Credentials(password=phrase),
               require_encrypted=True) as kristal:
    for entry in kristal.list():
        print(entry["path"], entry["size"])
```

A reader fully validates the stream, ZIP structure, manifest, hashes, and required signature policy **before** providing filenames or content. Temporary files are encrypted with an ephemeral key. RAM, swap, and compromised workstations remain outside this guarantee.

## Documentation

- [Usage and CLI](docs/USAGE.md)
- [Binary and cryptographic contract](docs/FORMAT.md)
- [Architecture and performance](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Recovery and incidents](docs/RECOVERY.md)
- [Python API](docs/API.md)
- [Ecosystem integration](docs/INTEGRATION.md)
- [Hardware and key-service providers](docs/PROVIDERS.md)
- [Technical decisions](docs/DECISIONS.md)
- [Release testing and qualification](docs/VALIDATION.md)
- [Primary references](docs/REFERENCES.md)
- [Security policy](SECURITY.md)

## Development

```sh
python -m pip install -c constraints.txt -e ".[dev]"
python -m pytest
python -m ruff check src tests tools
python -m ruff format --check src tests tools
python -m build
```

Constraints pin qualified runtime versions, not development tools or the hashes of every package. Read `docs/RELEASE.md` before production distribution.

## Boundaries

The manifest signs **physical bytes**. It creates no Logical Commitment, epistemic authority, or proof of truth. Packaging does not publish, activate, or synchronize anything. Sources are preserved; no other repositories are changed by this release.

The license is not chosen on behalf of the owner: see [LICENSE](LICENSE). The code is supplied for the owner's use and modification; third parties are not implicitly granted any open-source license.

## Satellite integration verification (October 27, 2026)

See [compatibility checks and qualification limits](docs/Integration-Verification-2026-10-27.md). External versions and statuses must be verified before any deployment.
