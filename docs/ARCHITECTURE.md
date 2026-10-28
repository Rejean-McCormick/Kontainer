# Architecture and performance

## Separation of responsibilities

Framework owns contracts and semantics. This repository implements a physical profile. Local Kit builds states; Manager orchestrates the experience and transport; readers consume authorized bytes. Konfid decides permissions in managed workflows. None of those roles is merged here.

| Module | Responsibility |
|---|---|
| `api.py` | Package transactions, verified reads, explicit extraction, rewrapping |
| `archive.py` | Selection, strict ZIP64, manifest, signatures |
| `crypto.py` | Envelope, slots, KDF, AEAD and secretstream |
| `staging.py` | Encrypted temporary storage, random-access reading |
| `filesystem.py` | Regular files, link rejection, atomic publication |
| `keys.py` | Typed keys, private-key encryption |
| `integration.py` | Local Kit projection without duplicating the semantic engine |
| `providers.py` | Application-injected provider interfaces |
| `cli.py` | Safe arguments and JSON results |

## Writing

Inventory → read files in chunks → ZIP STORE in encrypted temporary storage → verify structure and hashes → wrap → fsync new file → publish atomically.

Creation rejects destinations inside the source. It neither deletes nor modifies source files. It checks source identity/metadata before and after reading, and compares the final inventory. A concurrently modified source must be stabilized or captured by an OS snapshot; these checks do not replace a filesystem snapshot against an active local attacker.

Open mode is deterministic for identical paths/bytes and signature. Encrypted files deliberately differ with each write. `rewrap` preserves the exact inner ZIP, its signatures and any carried semantic states.

## Reading

Copy/decrypt to encrypted spool → verify authenticated finalization → precheck central directory → verify all members and manifest → verify signature policy → expose read-only view.

The source file can then close: the reader uses its private snapshot, not a second read from the original path. `inspect` reads only unauthenticated public claims and explicitly labels them as such.

## Temporary storage

`EncryptedSpool` writes 1 MiB chunks using XChaCha20-Poly1305, a random ephemeral 32-byte key, nonce `random16 || index_be64`, and domain/index AAD. Each chunk is written once. The last may be short. Expected position and size come from trusted memory. Encrypted storage supports the seeks required by ZIP without dumping plaintext to disk.

One decrypted chunk is cached; RAM use is largely limited to a few chunks, manifest and ZIP metadata, plus **64 MiB** during Argon2id. Python and libraries make memory copies; no guaranteed secret erasure is claimed. Temporary files are normally closed/deleted but may remain encrypted after a crash.

## Costs and deliberate trade-offs

- Creation: several local read/verification passes, O(total size), without loading everything into RAM.
- Opening: full O(total size) verification before first data; member access afterward through the spool.
- Rewrapping: fresh content key and complete re-encryption, not fragile header-only rotation.
- STORE: no compression, saving CPU and avoiding decompression bombs; modest structural/authentication overhead.
- No in-place modification; each result is a new snapshot.
- No millisecond guarantees for hundreds of GiB. A future encrypted partial-access profile would require a separate design and security review.

## Atomicity and OS

Files are prepared in the destination's parent directory and fsynced before publication. Without overwrite, publication uses an atomic hardlink that fails if the target exists. Filesystems without hardlinks do not get a racy fallback: the operation fails. `--overwrite` uses `os.replace`. The parent directory is fsynced on POSIX.

Source/destination parent directories must be trusted. Known symlinks and reparse points are rejected, but there is no absolute protection against an administrator or same-user process racing to replace directories.

Extraction is an explicit plaintext export into a **new** directory. It cleans up after ordinary errors, but a forced interruption can leave partial files. Extraction is not an atomic directory transaction. On Windows, POSIX modes 0600/0700 are not a substitute for a DACL: use a protected user/volume configuration.
