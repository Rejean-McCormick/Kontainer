# Primary references

References consulted for this release: October 11, 2026. These sources support the primitives and boundaries; they do not certify this repository.

- [libsodium secretstream](https://doc.libsodium.org/secret-key_cryptography/secretstream): authenticated streams, ordering, finalization, and rekeying.
- [libsodium sealed boxes](https://doc.libsodium.org/public-key_cryptography/sealed_boxes): X25519/XSalsa20-Poly1305, confidentiality without sender authentication.
- [RFC 9106 — Argon2](https://www.rfc-editor.org/info/rfc9106/): memory-constrained Argon2id profile, 64 MiB, t=3, p=4.
- [RFC 5869 — HKDF](https://www.rfc-editor.org/info/rfc5869/): extraction/expansion and known-answer vectors.
- [WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/): PRF extension, RP identity, authenticators. Integration reference, not a delivered provider.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html): factors, phishing resistance, non-exportability.
- [Microsoft TPM key attestation](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/component-updates/tpm-key-attestation): guarantees of a real hardware-protected key.
- [NIST FIPS 203 — ML-KEM](https://csrc.nist.gov/pubs/fips/203/final): basis for a future post-quantum profile, not implemented here.
- [age specification](https://c2sp.org/age): studied format, not claimed to be compatible.

Owner-supplied references: ecosystem instructions, `Kristal-Framework/docs/16_SECURITY_AND_CONFIDENTIALITY.md`, `spec/v9/Security-and-Confidentiality.md`, `spec/v10/Security-and-Confidentiality.md`, `Kristal-Authoring-Kit/tools/kristal.py`, `Kristal-Manager/README.md`, `konfid/SECURITY.md`, `Konfid.wiki/Security-Boundaries.md`, `interaction_kernel/docs/security-authority.md`.
