# `.kristal` file contract — v1 proposal

Status: profile implemented in `Kristal-Container 1.0.0rc1`, proposed for normative adoption and maintenance in **Kristal-Framework**. This document precisely specifies v1 reading behavior; adding protection requires a new specification and tests, never a silent fallback.

## 1. Envelope

| Bytes | Meaning |
|---|---|
| 0..7 | Magic: ASCII `KRISTAL` followed by hexadecimal `01` |
| 8..11 | JSON header length, unsigned 32-bit big-endian integer |
| next | Canonical UTF-8 header, 1 to 65,536 bytes |
| rest | Raw ZIP in open mode; authenticated frame sequence in encrypted mode |

JSON uses lexically sorted keys, `,` and `:` separators, no unnecessary whitespace, UTF-8 without BOM, `ensure_ascii=False`, no NaN/Infinity and no duplicate members. Normative numeric values are integers. This is a subset defined here, **not a claim of general RFC 8785/JCS conformance**. Alternative serialization is rejected. Undefined fields in normative objects are rejected.

Open mode: `{"format":"kristal.container/1","mode":"open"}`.

Encrypted mode: exact fields `format`, `mode=encrypted`, `profile=xchacha20poly1305-secretstream-v1`, `id` (16 random bytes), `stream` (24-byte secretstream header), `slots` (1 to 16). Binary JSON fields use standard RFC 4648 Base64 with canonical padding.

No logical identity or plaintext filename appears in this header. Visible information includes mode, algorithms, access types/counts, SHA-256 identifiers of recipient public keys, and total size. The profile provides no padding.

## 2. Content encryption

A fresh random **32-byte** key and new libsodium `crypto_secretstream_xchacha20poly1305` stream are generated on each encrypted creation/rewrap. Passwords never encrypt content directly.

Each frame is prefixed by its unsigned 32-bit big-endian length. Plaintext is split into 1,048,576-byte chunks, with a potentially shorter last data chunk. Each frame adds 17 libsodium bytes. Data tags are `TAG_MESSAGE=0`. An empty `TAG_FINAL=3` frame is **always** appended; its length is 17. No bytes follow this frame; no data chunk may follow a short chunk.

Associated data for each frame:

```
ASCII("kristal/stream/v1") || 00 || SHA256(magic || header_length_be32 || header_json)
```

The complete header, including all key access slots, is therefore authenticated by each frame. Readers require authenticated finalization: a partial sequence of individually valid chunks is not sufficient to accept a container.

## 3. Access slots

Slots provide **OR** access paths. At most one password slot (plain or with factor), one recovery slot, and no duplicate recipients. The writer allows up to 14 recipients plus password and recovery. The CLI is more restrictive to avoid accidental password/recipient combinations; the API allows explicit combinations.

### Password

`type=password`, `kdf`, `salt` (16 bytes), `nonce` (24), `wrapped` (48).

Exact KDF: `name=argon2id`, `version=19`, `memory_kib=65536`, `iterations=3`, `parallelism=4`, 32-byte output. Passphrase encoded in UTF-8 with no normalization or truncation. On creation: 15 to 1,024 characters and no more than 4,096 bytes. Alternative cost parameters are rejected before computing; they would require another profile.

Derive `D = Argon2id(password, salt)`, then `KEK = HKDF-SHA256(D, salt=container_id, info="kristal/password/v1", L=32)`.

Encrypt the content key using XChaCha20-Poly1305, random nonce, and AAD:

```
ASCII("kristal/keyslot/v1") || 00 || container_id || canonical(slot_without_wrapped)
```

### Password AND factor

Same fields with `type=password-factor`. Derive `D` as above, then `KEK = HKDF-SHA256(D || factor_32_bytes, salt=container_id, info="kristal/password-factor/v1", L=32)`.

The factor is a random secret or provided by an application-supplied `FactorProvider`. A plain secret file is copyable and does not prove hardware presence. The type certifies no MFA assurance; that depends on the qualified provider.

### Recovery

`type=recovery`, `nonce` (24), `wrapped` (48). Independent random 32-byte secret. `KEK = HKDF-SHA256(secret, salt=container_id, info="kristal/recovery/v1", L=32)`, then the same AEAD wrapping. The secret is never stored inside the container.

### X25519 recipient

`type=x25519`, `key_id=SHA256(public_key_32_bytes)` in lowercase hexadecimal, `wrapped` (96 bytes).

`wrapped = libsodium SealedBox(public_key, container_id || content_key)`. SealedBox uses standard libsodium X25519/XSalsa20-Poly1305; this slot algorithm is distinct from the stream cipher. Verify `container_id` after opening. A sealed box does not authenticate its sender; signatures serve a different purpose.

### HKDF

RFC 5869 SHA-256: `PRK=HMAC(salt, IKM)`, single output `HMAC(PRK, info || 01)` (32 bytes). Never reuse labels between domains.

## 4. Inner ZIP

Deliberately stricter than generic ZIP:

- Regular files only, `STORE`, no explicit directories; no links, auto-executables or NTFS streams.
- Relative UTF-8 NFC names, `/`, maximum 1,024 bytes; each component maximum 240 bytes.
- Reject `..`, `.`, empty components, backslashes, control/format characters, `:*?"<>|`, Windows reserved names, and trailing dots/spaces.
- No duplicates, case-folded aliases or file/directory conflicts; `_kristal` namespace reserved.
- Lexicographic order of user filenames; `_kristal/manifest.json` last.
- Fixed timestamp 1980-01-01 00:00:00; creator system Unix (3), external attribute `0o100600 << 16`.
- Local ZIP64 header version 45 for every member, descriptor flag (8), UTF-8 flag when needed; local CRC zero, local sizes `0xffffffff`.
- Exact local extra: ID 1, length 16, two null 64-bit sizes.
- Signed descriptor `PK\x07\x08`, CRC32, compressed and actual 64-bit little-endian size.
- No gaps, prefixes, overlap, comments or suffixes; no extras other than ZIP64.
- Central directory and EOCD/ZIP64 EOCD must be consistent and bounded before parser allocation.

CRC32 is not cryptographic protection. SHA-256 hashes in the manifest cover individual files; the authenticated stream protects encrypted packages. Ordinary ZIP archives must be converted by `pack` from an authorized directory rather than accepted directly.

## 5. Manifest and signature

Canonical manifest: `format=kristal.container-manifest/1`, `files=[{path,size,sha256}, ...]`, optional `signature`. Sizes are nonnegative integers, SHA-256 lowercase hexadecimal. Each non-manifest file appears exactly once; extra data is never ignored.

Signature exact fields: `algorithm=ed25519`, `public_key` (32 bytes), `value` (64 bytes).

```
signature = Ed25519.sign(
  ASCII("kristal/container-manifest/1") || 00 || canonical(manifest_without_signature)
)
```

The embedded key verifies cryptographic consistency but **cannot establish its own trust**. The application supplies trusted keys out-of-band. `require_signature=True` without any trusted key rejects every file. Providing trusted keys means a corresponding signature is mandatory.

The signature covers paths, sizes and contents via hashes, not the opening policy, exact physical ZIP or Framework Logical Commitment. A local `require_encrypted` policy and separate distribution authorization remain necessary. A trusted signing key does not authorize execution of the content.

## 6. Default limits

10,000 files, 8 GiB per file, 16 GiB total content, 8 MiB manifest, 16 MiB central directory, and 16 MiB direct `read()`. Temporary-space calculation includes bounded structural overhead. `copy_to()` handles large files in chunks. The `Limits` API can adjust these positive ceilings; increasing them increases the resources granted to a hostile import.

## 7. Key files

Canonical `kristal.key/1` format. `kind` distinguishes `identity`, `signing`, `recipient`, `verify`, `recovery`, and `factor`. Raw key material is 32 bytes.

Identity/signing private keys must be encrypted on disk: same Argon2id, then `_password_key` with fixed domain identifier `b"kristal-key-v1\x00\x00"`, XChaCha20-Poly1305, AAD `b"kristal/keyfile/v1\x00" || canonical(object_without_encrypted)`. Fields: format, kind, kdf, salt, nonce, encrypted. Recovery/factor secrets and public keys use Base64 `data`; the former must be stored separately and protected.

Confidentiality of a key file does not guarantee a hardware non-exportable key.
