# Branch 03 — Final-system release, distribution and exploration

**Document class:** `TARGET_DESIGN` + bounded `SOURCE_OBSERVED` checks, 2026-11-09. **Not** a claim of production deployment or approved publication. This document coordinates FC-05/06/18/19 while the owning repository retains authority for its code, contracts and decisions.

## End-to-end functional chain

```text
Owner-controlled local Kristal workspace / candidate
    → Manager: instance inventory and scoped staging, no implicit public write
    → KristalDiag: independent, exact-input diagnostic verdict
    → Actual content owner: separate permission to disclose selected bytes
    → C2/C3 gate and authorized publisher: immutable public collection receipt
    → readers: Konstellation, Konstellation Light (verified derived views)

Alternative private/offline path:
    approved local read-surface projection → Kontainer integrity/encryption
        → explicitly authorized offline reader/import (no publication)

Konstellation Publisher: CODE-ONLY local bundle and simulated rollback;
        NOT a live publisher until independently qualified/authorized.
```

**Key boundaries:** a local Kit build is not C1 qualification; a diagnostic verdict is not C2 owner consent; C3 byte integrity is not permission to publish; a Git commit is not content authorization; a transport hash is not semantic truth; a reader import is not activation; local rehearsals are not observed VPS deployments. All public disclosures require review before any remote Git staging/push.

**Relevant exact existing contracts:** `kristal.github-read-surface/1.0`, `kristal.github-sync-manifest/1.0`, `kristal.github-collection-index/1.0`, and local product-specific schemas when accepted. These are observed profile IDs, not a declaration that Framework v10 and v11 are intercompatible. Framework v11/Kit v4 qualification remains a separate cross-branch decision.

## Repository responsibility and target handoff

**Sole responsibility:** physical byte-integrity, optional encryption, recovery and portable file packaging, not semantic canonization, hosting or signing legitimate C2 grants.

**Current implementation evidence:** `src/kristal_container/integration.py` has `pack_read_surface` requiring the exact `kristal.github-read-surface/1.0` projection, ready status, complete path/hash/byte budget agreement and member immutability. No remote write is performed.

**Target interfaces:** Kit/Manager approved local read-surface → portable integrity-checked container → an independent verifier/reader; release classification and recipient rights are caller decisions.

**Acceptance:** tampered input rejection, bad member path, duplicate member conflict, wrong password/recovery key, explicitly allowlisted recipient and recovery tests; any public export also requires a separate owner publication grant.

**Snapshot constraints:** this environment has no installed `PyNaCl` (`nacl`) dependency, so runtime tests could not be collected. Do not interpret successful source inspection as cryptographic qualification.

## Cross-repository owner work still pending

- Agree exact qualified Framework/Kit/release profile and visibility classification, including v11 read-projection compatibility where adopted.
- Define producer and consumer revision pins and run the same accepted/denied fixtures at both endpoints before calling a boundary qualified.
- Keep public Git and Pages writes blocked until legitimate owners independently approve exact data/audience, proof issuers are verified, and rollback has real deployment evidence.
- The cross-repository synthetic C3→Light test lives in the branch-level integration bundle; it proves integrity and format compatibility for one fixture **only**, not real publication or full reader compatibility.

## Coordination

This repository is one of the **seven** Branch 03 owner repositories. The central `kOA-Digital-Ecosystem` FC-05/06/18/19 pages are architectural intent and cannot replace owner normative code/contracts. See branch-level `HANDOFF.md` and `BRANCH_REPORT.md` supplied alongside the updated archives.
