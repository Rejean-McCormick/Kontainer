# Sécurité

Ce dépôt traite des secrets. Lire `docs/THREAT_MODEL.md`, `docs/FORMAT.md` et `docs/VALIDATION.md` avant de lui confier des données sensibles de production.

## État

Implémentation candidate, tests locaux effectués, **pas d'audit indépendant**. Aucun claim FIPS, certification MFA/AAL, compatibilité age, qualification TPM ou garantie postquantique. Les capacités absentes ne sont pas activées automatiquement.

## Signalement

Ne pas publier de clés, mots de passe, données privées ou preuve d'exploitation contenant ces éléments dans une issue publique. Transmettre au propriétaire du dépôt par un canal privé déjà établi. Aucun faux contact de sécurité ou adresse inexistante n'est fourni ; le propriétaire doit configurer le canal avant publication publique.

## Changements exigeant une revue de sécurité

- Format, signature, key slots, KDF, AAD, nonces et framing.
- Parser ZIP, chemins, limites, canonicalisation et allocation mémoire.
- Fournisseurs matériels ou réseau, identité et autorisation.
- Récupération, export en clair, cache, temporaires et journalisation.
- Dépendances crypto, packaging, CI et distribution.

## Invariants

Ne pas supprimer une vérification pour faire passer un test. Aucun downgrade silencieux. Aucun secret dans les arguments/logs. Aucun import ou exécutable choisi par le contenu. Aucun octet métier exposé avant vérification requise. Aucun fichier existant écrasé sans option explicite. Aucun secret réel dans les fixtures ou archives de livraison.

## Maintenance

Revoir les avis de vulnérabilité des versions Python, PyNaCl/libsodium, argon2-cffi et de leurs bindings. Mettre à jour les contraintes par changement revu et rejouer les tests. Une dépendance figée n'est pas une preuve d'absence de vulnérabilité.
