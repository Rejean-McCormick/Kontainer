# Architecture decisions

## ADR-001 — Engine in a separate repository

One reusable engine for Authoring Kit, Manager and readers. Framework owns the format; this repository owns its implementation. Avoid duplicate cryptographic code and maintain independent security tests. No mandatory service.

## ADR-002 — STORE and authenticated envelope

Inner ZIP64 STORE groups files without compression. The encrypted outer envelope also hides names. Reject legacy ZIP encryption and UI-only password checks. The outer format is not directly openable by 7-Zip, even in open mode: the extension denotes a versioned Kristal envelope.

## ADR-003 — Proven libraries, explicit protocol

libsodium via PyNaCl for secretstream, AEAD, sealed boxes and Ed25519; argon2-cffi for the exact RFC 9106 Argon2id profile. Primitives are not reimplemented. The short HKDF-SHA256 bridge follows RFC 5869 and has a known-answer test. Application-level composition is still new and needs its own review; using libsodium is not an audit of the container.

The `age` format was considered. Its standard password profile uses scrypt and cannot freely mix it with other stanzas. AND-factor requirements, recovery, Kristal profiles and application limits would require extensions. This repository does not claim `age` compatibility or change its specification; it documents the review cost of its own envelope honestly.

## ADR-004 — OR slots; AND factor within a slot

Password and factor must both participate in cryptographic derivation. A separate password-only entry would negate that property. Recovery is intentionally an alternative path; `inspect` displays its existence without revealing its secret.

## ADR-005 — No fake hardware lock

No MAC address, system ID, disk serial or simulated TPM presented as hardware binding. Explicit provider interfaces, qualification on real hardware before enabling. The file itself loads no plugin or command.

## ADR-006 — Full validation and encrypted temporary files

No private preview or filenames before full verification. An encrypted spool provides ZIP parser random access without creating a complete plaintext disk copy. Accepted cost: linear initial read; a partially decryptable index would be a separate profile if warranted.

## ADR-007 — Immutable sources and transactional writes

No in-place editing. Sources remain intact. Fresh key on every rewrap. Publish prepared files through an atomic primitive; no implicit migration, deletion, sync or activation.

## ADR-008 — Post-quantum and blockchain

ML-KEM is a relevant standardized direction for long-lived secrets. It is not enabled by adding a label. A future hybrid profile must also protect recovery access and be qualified using maintained libraries and independent vectors. Unknown slots are never ignored.

Blockchain does not address the main threats: copying, lost keys and local leaks. Signatures and independent audits belong to separate layers. No consensus network or blockchain dependency is added.
