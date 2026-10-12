# Fournisseurs externes : frontières et qualification

Les deux interfaces Python sont opérationnelles, couvertes par des doubles de test. **Aucun fournisseur TPM, WebAuthn, KMS ou Konfid de production n'est inclus.** L'absence de matériel/infrastructure qualifiée n'est jamais remplacée par une clé logicielle silencieuse. `capabilities` garde ces intégrations dans `unsupported`.

## FactorProvider

`derive(container_id: bytes) -> bytes` retourne exactement 32 octets secrets pseudorandom. L'identifiant aléatoire du conteneur a 16 octets, permet de distinguer ses facteurs et doit conduire au même résultat lors des réouvertures. Le résultat est combiné à Argon2id via HKDF ; aucun slot mot de passe simple n'est ajouté.

Usage : `Protection(password=..., factor_provider=provider)`, puis `Credentials(password=..., factor_provider=provider)`.

Pour WebAuthn PRF : qualifier une origine/RP ID stable, l'enrôlement, le support PRF réel, la vérification utilisateur, le stockage des identifiants de credential hors enveloppe, la restauration et les conséquences des passkeys synchronisées. Une passkey synchronisée n'est pas une liaison à un unique appareil. Ne jamais utiliser une signature publique comme secret de chiffrement. Un code TOTP n'a pas l'entropie d'un secret de déchiffrement autonome.

Pour TPM : lier l'accès à une clé protégée par le TPM réel, vérifier l'absence de migration/export requis, traiter mises à jour et réinitialisations, qualifier le chemin de récupération. Tous les TPM ne supportent pas X25519 : le slot destinataire existant ne doit pas être présenté comme un wrapper universel TPM. Un nouveau slot d'encapsulation peut nécessiter une nouvelle version de profil.

Le protocole Python n'atteste pas les propriétés d'un fournisseur. C'est une frontière de confiance explicite pour l'application, pas un label de sécurité auto-déclaré par le fichier.

## RecipientResolver

`unwrap(key_id, container_id, wrapped, header_sha256) -> bytes | None` reçoit une sealed box X25519. Le callback n'est appelé que pour les identifiants présents dans `Credentials.allowed_recipient_ids`, fixés par l'application. Il retourne le plaintext `container_id || content_key` (48 octets), ou None pour une clé non gérée. Les erreurs remontent ; aucun endpoint ou module n'est chargé depuis le fichier.

Un fournisseur géré doit vérifier l'acteur et le workload via son IdP, demander une décision courante et bornée à Konfid/policy runtime, vérifier le scope et les approbations nécessaires, puis faire exécuter le déballage par son service de clés. Les champs de l'en-tête sont des **assertions non authentifiées** jusqu'à la validation du flux ; ils ne peuvent pas être leur propre autorisation.

Le callback doit imposer délais, budgets, isolation par tenant, journalisation minimale et absence de retour de secrets dans les traces. La clé privée ne doit pas être envoyée au client. Même si seule la clé de contenu revient au client, celui-ci peut la conserver : ne pas promettre de révocation rétroactive.

Une décision d'autorisation avant livraison de clé ne remplace pas le chiffrement, et un wrapper de récupération qui ouvre sans serveur constitue un bypass **volontaire**, à traiter comme tel dans la politique d'organisation.

## Critères de qualification d'un fournisseur

- Succès réel sur matériel/infrastructure cible et échec sur un autre appareil non autorisé.
- Échec fermé si facteur, serveur ou preuve d'autorité manque ; aucun fallback implicite.
- Mot de passe seul insuffisant pour le profil ET.
- Restauration sur un appareil neuf avec le seul moyen de récupération prévu.
- Réenrôlement et renouvellement des accès, sans changer les octets de l'état logique.
- Résistance au rejeu/confusion de tenant dans le parcours serveur.
- Contrôle des caches, journaux, descripteurs et cycle de vie des secrets.
- Revue indépendante de l'assemblage et des assurances affichées.

Une simulation qui passe ces interfaces ne suffit pas à cocher les tests matériels.
