# Kontainer — consolidation report (October 27, 2026)

## Decision

**One canonical source repository: `Kontainer` (`kristal-container` v1.0.0rc1).**
The two ZIP files examined are **not two engines or two product generations**. They share **58 files that are byte-for-byte identical**. No code merge is required.

### Contribution of each archive

- `znapshot_Kontainer_10271324.zip`: 61 source files, including `GitSink.bat`, `ZmartZnap.pyw`, and `SNAPSHOT_INDEX.txt`, exclusive to this archive.
- `kontainer.zip`: the same 58 common files, plus two Python distributions under `dist/` (`.whl` and `.tar.gz`).
- The consolidated ZIP contained the **exact union of the 63 original files**, plus this report and a manifest of their hashes. No original application file was modified.

### Checks performed during that consolidation

- CRC integrity of both input ZIPs and per-file SHA-256 comparison: **58/58 common files identical**.
- **13 Python modules** in the wheel identical to the snapshot's `src/kristal_container/*.py`.
- Files shared between the sdist and sources: identical bytes (generated metadata is not an engine modification).
- Wheel: **18/18 hashes** in its `RECORD` file verified.
- Python syntax checks on **21 files** (sources, tests, tools), **7 valid JSON files** and **2 valid JSON Schemas**.
- Consolidated ZIP re-extracted and verified against the SHA-256 manifest.

### Verification limits

**Functional tests were not rerun during the consolidation session.** PyNaCl and required dev dependencies were unavailable locally, and PyPI download failed. Historical `docs/VALIDATION.md` reports **62 passing tests on October 11, 2026** in its own environment; this historical evidence is not a new test result.

The format, cryptography and protocol remain a **release candidate without independent cryptographic audit**. No claims of Windows, TPM/WebAuthn/KMS, sensitive-production, or Framework-certification qualification are added.

## Preserved organization

```text
Kontainer/
  src/kristal_container/  ← single library source
  tests/                  ← existing tests, unchanged
  contracts/              ← identical schemas, unchanged
  docs/                   ← original documentation + this report
  dist/                   ← provided wheel and sdist, not rebuilt
  examples/               ← original examples
  .github/                ← original CI
  CONSOLIDATION_SHA256.json
```

`dist/` is already in `.gitignore` and must not become a second repository. Previously delivered packages are retained **as distributable artifacts**, not as a second source of truth. `SNAPSHOT_INDEX.txt` preserves the original snapshot state; use `CONSOLIDATION_SHA256.json` for that consolidation.

## Careful local installation

1. Back up **both existing directories** and their configuration before deleting or replacing anything.
2. Choose **one** canonical code directory (e.g. `C:\mycode\Kontainer`). Preserve the active branch's `.git` directory if present, and compare local modifications not included in the ZIPs.
3. Extract the consolidated ZIP into that code repository (not a `.kristal` data area). Do not replace or move containers, keys, secrets or private content.
4. To validate operation, create a virtual environment and run `python tools/check.py` **after installing dependencies from `constraints.txt`**.
5. After comparison and Windows verification, optionally archive the redundant old directory. **Do not delete it automatically**, since its local data is not in the ZIP files.

## Unchanged elements

API, CLI, envelope formats, encryption, signatures, recovery, adapters, schemas, tests, workflow and version `1.0.0rc1`. No data, GitHub repository, key file, or real container was modified by that consolidation.
