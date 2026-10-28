# Threat model

## Guarantees and limitations

| Adversary / event | Control | Limitation |
|---|---|---|
| Copy of encrypted file | Random key, AEAD, memory-hard KDF | Weak password susceptible to offline attack |
| Modification/truncation/reordering | Authenticated header, per-frame tags, mandatory FINAL | A keyholder can produce other valid content |
| Malicious open file | Strict parser, bounds, manifest | Unsigned manifest cannot prove origin |
| Forged provenance | Signature and externally trusted keys | No automatic factual truth or semantic authority |
| Hostile archive | STORE only, validated paths/sizes/counts | Allowed CPU/disk budget can still be exhausted |
| Temporary-file leakage | Encrypted spool with ephemeral key | RAM/swap/core dumps out of scope |
| Lost access method | Independent recovery slot | No magic recovery without a configured method |
| Reintroduction of old version | `expected_sha256` from trusted source | File alone cannot know newest version |
| Compromised workstation during reading | No comprehensive control in this repo | Authorized plaintext may be copied |
| Lost device | Rewrap and new keys for future use | Previously decryptable copies are not revoked |
| Managed service unavailable | Failing provider, no implicit fallback | Recovery slot is an intentional alternative path |

## Assets

Content, filenames, inner metadata, content keys, passphrases, private identities, factors and recovery keys. Confidential logical fingerprints must remain in the encrypted portion. Recipient IDs and file size are acknowledged leakages in the v1 profile.

## Out of scope

Unbreakable DRM, protection against root/administrators, guaranteed erasure of SSDs or Python memory, hiding file sizes, retroactive revocation of plaintext, a trustworthy offline clock, proof of truth, complete antivirus, renderer safety or prompt injection after decryption.

Signed content is still untrusted input for HTML, PDFs, macros, scripts and AI models. The reader neither renders nor executes anything. Application ACLs/Reader Policies must still be enforced before search, caching, citation and export.

## Operational controls

Use a long, unique passphrase; a minimum length is not an entropy test. Protect the machine and system disk, limit core dumps, protect swap and user accounts. Keep recovery secrets and factors away from the relevant files. Lower limits on exposed services and limit concurrency (each Argon2 operation consumes 64 MiB). Do not send `Credentials` objects to logging.

The engine has no offline rate limiter: an attacker may copy the file and modify the reader. A purported local attempt limit would be misleading. Online providers must enforce their own limits and policies.

## Downgrades and authenticity

Envelope authentication protects against unauthorized changes. However, an actor authorized to decrypt may distribute an open version of the same signed content. Consumers that require confidentiality must enforce `require_encrypted=True` through an external policy. A manifest signature does not sign the recipient list.

A valid signature with an embedded key is only `valid-untrusted`. Trusted keys must be authenticated/distributed separately. No automatic trust-on-first-use bootstrapping occurs.
