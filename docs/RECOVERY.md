# Recovery, rotation and incidents

## Before losing access

1. Generate an independent recovery secret (`keygen recovery`).
2. Explicitly add it when creating the container.
3. Copy the container to a test location and verify it opens **using recovery alone**.
4. Keep the recovery secret elsewhere with a separate protected backup.
5. Document who may use it; it allows decryption without the normal password or factor.

Both a container backup and a secret backup are required. The engine cannot recover lost bytes if every copy of the file is gone.

## Forgotten password or lost factor

Open using `--unlock-recovery`, then `rewrap` into a new file with new protection. Verify the new file using both the normal and recovery paths before changing operational references. Retain source/previous copies according to policy; do not claim automatic secure erasure.

## Broken device

The engine exposes an external factor interface but does not ship native TPM locking. When a qualified hardware provider is used, its normal access path must include a tested recovery slot **before** activation. Replacing a device creates a new envelope and new access parameters; the Logical Commitment remains unchanged.

No system ID, MAC, serial number or universal shared fallback secret is used. Recovery is controlled by the owner or organizational policy, never a hidden software backdoor.

## Compromise

- Suspected opening-secret compromise: create a new content key via `rewrap`, and distribute the new version to authorized users.
- Compromised recipient identity: remove that recipient from the new envelope; create a new identity if needed.
- Compromised signing key: revoke its trust in readers; qualify and sign new content with a different key. `rewrap` preserves an existing signature and is therefore not a new signature.
- Compromised recovery method: create independent new recovery material and a new file.

Encryption cannot revoke knowledge already obtained. Old copies and exported data may remain readable. A key service may reject **new** key deliveries but cannot erase keys already retrieved by a client.

## Organizations and quorum

Konfid may govern decisions; Orgo may gather approvals; a KMS/HSM performs cryptographic operations; Interaction Kernel maintains execution boundaries and receipts. User passwords, recovery secrets and content must not enter audit events.

An approval quorum is not cryptographic secret sharing. A 2-of-3 scheme is not implemented here: use a proven solution with renewal, custodian management and recovery tests before claiming that assurance.
