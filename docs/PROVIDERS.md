# External providers: boundaries and qualification

Both Python interfaces are functional and covered by test doubles. **No production TPM, WebAuthn, KMS or Konfid provider is included.** Missing qualified hardware/infrastructure is never silently replaced by a software key. `capabilities` keeps these integrations marked `unsupported`.

## FactorProvider

`derive(container_id: bytes) -> bytes` returns exactly 32 pseudorandom secret bytes. The random container ID is 16 bytes, distinguishes factors between containers and must lead to the same result on reopening. The result is combined with Argon2id through HKDF; no plain password-only slot is added.

Usage: `Protection(password=..., factor_provider=provider)`, then `Credentials(password=..., factor_provider=provider)`.

For WebAuthn PRF: qualify a stable origin/RP ID, enrollment, actual PRF support, user verification, credential-ID storage outside the envelope, restoration, and the implications of synchronized passkeys. A synchronized passkey is not bound to a single device. Never use a public signature as an encryption secret. A TOTP code lacks the entropy of an independent decryption secret.

For TPM: bind access to a key protected by the real TPM, verify migration/export requirements, handle updates and resets, and qualify recovery. Not all TPMs support X25519: the existing recipient slot must not be described as a universal TPM wrapper. A new encapsulation slot may need a new profile version.

The Python protocol does not attest provider properties. It is an explicit application trust boundary, not a self-declared security label in the file.

## RecipientResolver

`unwrap(key_id, container_id, wrapped, header_sha256) -> bytes | None` receives an X25519 sealed box. The callback is invoked only for IDs listed in application-defined `Credentials.allowed_recipient_ids`. It returns plaintext `container_id || content_key` (48 bytes), or None for an unmanaged key. Errors propagate; the file never loads an endpoint or module.

A managed provider must authenticate the actor and workload through its IdP, request a current, bounded decision from Konfid/runtime policy, validate scope and required approvals, and have its key service perform unwrapping. Header fields are **unauthenticated claims** until stream verification; they cannot authorize themselves.

The callback must enforce timeouts, budgets, tenant isolation, minimal logging and no leaked secrets in traces. Private keys should not be sent to clients. Even when only the content key is returned, a client can retain it: do not promise retroactive revocation.

An authorization decision before key delivery does not replace encryption, and a recovery wrapper that opens without a server is a **deliberate** bypass to account for in organizational policy.

## Provider qualification criteria

- Success on real target hardware/infrastructure, failure on another unauthorized device.
- Fail closed when factor, server or authority evidence is absent; no implicit fallback.
- Password alone insufficient for the AND profile.
- Restoration on a new device using only the intended recovery method.
- Reenrollment and access renewal without changing logical-state bytes.
- Replay and tenant-confusion resistance in the server workflow.
- Controls on caches, logs, descriptors and secret lifecycle.
- Independent review of composition and displayed assurances.

Passing a simulation through these interfaces is not sufficient to mark hardware tests complete.
