# Python API

Paths accept `pathlib.Path` (or path-convertible values for the main API). Expected exceptions derive from `ContainerError` and carry a stable `code`.

## Creating containers

```python
pack(source, destination,
     protection=Protection(),
     selected=None,
     signing_key=None,
     allow_sensitive=False,
     overwrite=False,
     limits=Limits(),
     expected_members=None)
```

`selected` is a tuple of exact relative paths. `None` scans the directory; `()` creates a container without user files. `signing_key` is a 32-byte Ed25519 seed managed in memory by the caller. `expected_members`, reserved for verified integrations, contains sorted `path,size,sha256` records: the produced snapshot must match exactly before publication.

`Protection(password=None, factor=None, factor_provider=None, recipients=(), recovery=None)` is immutable. Binary secrets are 32 bytes. `recipients` holds X25519 public keys. `factor` and `factor_provider` are mutually exclusive and require a password. The different slots are **OR** access methods. Empty protection creates an open file.

## Reading containers

```python
with Container(path,
               credentials=Credentials(),
               limits=Limits(),
               trusted_signers=(),
               require_signature=False,
               require_encrypted=False,
               expected_sha256=None) as reader:
    report = reader.report
    entries = reader.list()
```

`Credentials` accepts `password`, `factor`, `factor_provider`, `identity`, `recovery`, `recipient_resolver`, and `allowed_recipient_ids`. Its secrets are omitted from `repr`. An object should not be shared between threads; the application controls its lifecycle.

- `read(relative_path) -> bytes`: bounded by `max_read_bytes`.
- `copy_to(relative_path, binary_stream)`: chunked export; the caller must validate the destination.
- `extract(new_directory)`: explicit plaintext export to a nonexistent destination, no overwrite.
- `rewrap(destination, protection=..., overwrite=False, allow_plaintext=False)`: preserves ZIP content and renews key and stream.
- `list() -> list[dict]`: copies records without exposing the internal mutable manifest.
- `close()`: closes ZIP and encrypted temporary files; no guarantee of erasing Python memory.

`expected_sha256` refers to the physical hash of the **entire** file. It protects against rollback only if the consumer gets it from trustworthy external state. It changes after rewrapping. `manifest_sha256` describes manifest bytes, not the Kristal's logical identity.

## Reports

The verified report distinguishes `integrity=verified`, `signature=absent|valid-untrusted|trusted`, `mode`, item count and size, manifest hash, signer ID, and `semantic_validation=not-performed`. The reader adds `container_sha256`; `pack` returns a verified snapshot report prior to enveloping.

`inspect_header(path)` reads only the public header and returns `verified=False`. It cannot be used to decide that a file is safe or its key slots authentic.

## Errors

| Type | Code |
|---|---|
| `FormatError` | `invalid-format` |
| `IntegrityError` | `integrity-failed` |
| `AccessError` | `access-denied` |
| `PolicyError` | `policy-denied` |
| `LimitError` | `limit-exceeded` |
| `UnsupportedError` | `unsupported-profile` |

An access error can result from an incorrect secret **or** a damaged envelope. Do not promise users these can always be distinguished. OS and application-provider errors may also propagate; callers must handle them without weakening security.
