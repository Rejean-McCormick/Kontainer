# Références primaires

Consultation pour cette livraison : 11 octobre 2026. Ces sources justifient les primitives et frontières ; elles ne certifient pas ce dépôt.

- [libsodium secretstream](https://doc.libsodium.org/secret-key_cryptography/secretstream) : flux authentifiés, ordre, fin et rekey.
- [libsodium sealed boxes](https://doc.libsodium.org/public-key_cryptography/sealed_boxes) : X25519/XSalsa20-Poly1305, confidentialité sans identité d'expéditeur.
- [RFC 9106 — Argon2](https://www.rfc-editor.org/info/rfc9106/) : profil Argon2id mémoire réduite 64 Mio, t=3, p=4.
- [RFC 5869 — HKDF](https://www.rfc-editor.org/info/rfc5869/) : extraction/expansion et vecteurs connus.
- [WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/) : extension PRF, identité RP, authentificateurs. Référence d'intégration, pas fournisseur livré.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) : facteurs, résistance au phishing, non-exportabilité.
- [Microsoft TPM key attestation](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/component-updates/tpm-key-attestation) : garanties d'une vraie clé protégée matériellement.
- [NIST FIPS 203 — ML-KEM](https://csrc.nist.gov/pubs/fips/203/final) : base d'un futur profil postquantique, non implémenté ici.
- [age specification](https://c2sp.org/age) : format étudié, non revendiqué comme compatible.

Références fournies par le propriétaire : instructions de l'écosystème, `Kristal-Framework/docs/16_SECURITY_AND_CONFIDENTIALITY.md`, `spec/v9/Security-and-Confidentiality.md`, `spec/v10/Security-and-Confidentiality.md`, `Kristal-Authoring-Kit/tools/kristal.py`, `Kristal-Manager/README.md`, `konfid/SECURITY.md`, `Konfid.wiki/Security-Boundaries.md`, `interaction_kernel/docs/security-authority.md`.
