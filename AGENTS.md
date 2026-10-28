# Instructions for contributors and agents

- Maintain separation between logical state and physical representation.
- Keep cryptographic primitives in maintained libraries; document every new protocol or profile.
- An unavailable protection must fail closed. No fake TPM, secret system ID, visual 2FA, or misleading post-quantum crypto labels.
- Never write real secrets to this repository or logs. Public binary fixtures must contain only synthetic open data.
- All imported files are untrusted. Preserve budgets, canonicalization, path rejections, signatures, and full verification.
- Every security change needs a threat-focused test, not merely a test that mirrors the implementation.
- No implicit publication, activation, migration, or synchronization in tools.
- Update FORMAT, schemas, vectors, capabilities, and VALIDATION when guarantees change.
- Clearly distinguish locally tested, test-double-tested, projected, and unqualified capabilities.
- Commands: `python -m pytest`, `python -m ruff check src tests tools`, `python -m ruff format --check src tests tools`, `python -m build`.
