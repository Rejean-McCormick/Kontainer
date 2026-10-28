# Kristal integration

## Observed state of supplied attachments

The supplied code includes Framework, Authoring Kit and Manager in `Kristal-Manager(1).zip`. Local Kit has `pack` and `pack-ai` commands that use `ZIP_DEFLATED`. Its `kristal.github-read-surface/1.0` projection lists `path`, `size`, `sha256` prefixed with `sha256:`, `ready`, `errors`, count and volume. Manager consumes the projection. Konfid neither stores nor verifies human passwords.

This repository is added separately. None of those repositories is modified, and these tools perform no canonical migration or GitHub synchronization.

## Contracts to adopt

| Owner | Intended integration change |
|---|---|
| Framework | Adopt/qualify `FORMAT.md`, schemas and vectors; preserve identity/representation separation |
| Authoring Kit | Add an export adapter that uses this library after its existing validation/build process |
| Manager | Add opening/protection/recovery, display verified status and prevent inadvertent plaintext export |
| Kompiler / readers | Read through `Container`, then enforce Reader Policies before any derived view |
| Konfid | Make access decisions for an external key provider, not process local passwords |
| Interaction Kernel | Bounded commands and receipts without equating them to semantic validation |

Repository schemas do not replace State Snapshot schemas. No Framework Logical Commitment recomputation is claimed here.

## Local Kit: usable adapter

The caller obtains the projection using its existing interface:

```sh
python tools/kristal.py read-surface PATH --require-ready --compact
```

Pass the decoded object to the adapter:

```python
from pathlib import Path
from kristal_container import Protection
from kristal_container.integration import pack_read_surface

# projection comes from the authorized Local Kit and is obtained by the caller.
pack_read_surface(Path("workspace"), Path("read.kristal"), projection,
                  protection=Protection(password=secret_passphrase))
```

The adapter requires `ready=true` and `errors=[]`, uses **exactly** the listed files, and compares sizes/hashes against the packaged snapshot before publishing the result. It runs no build, shell or network operation. The caller establishes projection provenance; the adapter does not requalify its `surface_digest` or semantics.

`materialization_objects` blobs are not downloaded. The file represents this selected surface, not a guarantee that every external Kristal reference is available offline. To include other authorized materializations, the owner must explicitly define a different package scope.

## Manager

Display separately: open/encrypted; signature absent/unknown/trusted; physical/Framework validation; normal/recovery access path. Never display “verified” based only on `inspect`.

Synchronizing an encrypted file transports opaque bytes. Exporting its plaintext surface, even to a private repository, requires an explicit policy and action. Third-party preview libraries, indexes, logs, caches and backups must respect the same confidentiality scope.

Do not automatically publish a confidential logical identifier in collection indexes. The host GitHub repository and its visibility are not a cryptographic guarantee.

## Readers

The library has no per-member ACL. Opening grants the process access to the entire package. If reader categories require incompatible permissions, produce separate packages/key domains and retain external semantic relations. A JSON permission field cannot prevent a keyholder from extracting bytes.

## Expected end-to-end verification

State built and validated by Local Kit → packaging → independent read → identical state bytes and references → fresh Framework validation using existing tools. This repository's byte-equality test does not recompute Framework semantics.
