# Récupération, rotation et incidents

## Avant la perte

1. Générer un secret de récupération indépendant (`keygen recovery`).
2. L'ajouter explicitement à la création du conteneur.
3. Copier le conteneur vers un emplacement de test et vérifier l'ouverture **uniquement** avec la récupération.
4. Conserver le secret de récupération ailleurs, avec une seconde sauvegarde protégée.
5. Documenter qui peut l'utiliser ; il permet le déchiffrement sans mot de passe ou facteur normal.

Une sauvegarde du conteneur et une sauvegarde du secret sont toutes deux nécessaires. Le moteur ne peut pas récupérer des octets perdus si toutes les copies du fichier ont disparu.

## Mot de passe oublié ou facteur perdu

Ouvrir avec `--unlock-recovery`, puis `rewrap` vers un nouveau fichier avec une nouvelle protection. Vérifier le nouveau fichier avec le chemin normal et le chemin de secours avant de remplacer les références opérationnelles. Conserver les sources/anciennes copies selon la politique de rétention ; ne pas prétendre à un effacement sûr automatique.

## Appareil cassé

Le moteur expose l'interface de facteur externe, mais ne livre pas un verrou TPM natif. Lorsqu'un fournisseur matériel qualifié sera utilisé, son chemin normal doit être accompagné d'un slot de récupération testé **avant** l'activation. Le remplacement d'appareil produit une nouvelle enveloppe et de nouveaux paramètres d'accès ; le Logical Commitment ne change pas.

Aucun system ID, MAC, numéro de série ou secret partagé de secours universel n'est utilisé. La récupération est détenue par le propriétaire ou sa politique organisationnelle, jamais par un backdoor caché du logiciel.

## Compromission

- Secret d'ouverture suspect : générer une nouvelle clé de contenu par `rewrap`, distribuer la nouvelle version aux personnes autorisées.
- Identité destinataire compromise : retirer ce destinataire de la nouvelle enveloppe, créer une nouvelle identité si nécessaire.
- Clé de signature compromise : retirer sa confiance dans les lecteurs ; qualifier et signer les nouveaux contenus avec une autre clé. Un `rewrap` préserve la signature existante et n'est donc pas une nouvelle signature.
- Récupération compromise : nouvelle récupération indépendante et nouveau fichier.

Le chiffrement ne retire pas une connaissance déjà acquise. Les anciennes copies et les données exportées restent potentiellement lisibles. Un service de clés peut refuser les **nouvelles** délivrances, sans effacer les clés déjà obtenues par un client.

## Organisation et quorum

Konfid peut gouverner la décision ; Orgo peut recueillir des approbations ; un KMS/HSM réalise l'opération cryptographique ; Interaction Kernel garde la frontière d'exécution et les reçus. Le mot de passe utilisateur, le secret de récupération et le contenu ne doivent pas entrer dans les événements d'audit.

Un quorum d'approbations n'est pas un partage cryptographique de secret. Le schéma 2-sur-3 n'est pas implémenté ici : employer une solution éprouvée, avec gestion du renouvellement, des détenteurs et tests de restauration, avant de prétendre à cette assurance.
