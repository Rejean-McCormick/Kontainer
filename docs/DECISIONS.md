# Décisions d'architecture

## ADR-001 — Moteur dans un dépôt séparé

Un seul moteur réutilisable par Authoring Kit, Manager et lecteurs. Le Framework possède le format ; le dépôt possède son implémentation. Éviter les copies de code de chiffrement et conserver des tests de sécurité indépendants. Aucun service obligatoire.

## ADR-002 — STORE et enveloppe authentifiée

ZIP64 STORE intérieur pour regrouper sans compresser. L'enveloppe extérieure chiffrée protège aussi les noms. Refus du chiffrement ZIP historique et du simple contrôle de mot de passe en interface. Le format extérieur n'est pas un ZIP directement ouvrable par 7-Zip, même en mode ouvert : l'extension désigne une enveloppe Kristal versionnée.

## ADR-003 — Bibliothèques éprouvées, protocole explicite

libsodium via PyNaCl pour secretstream, AEAD, sealed boxes et Ed25519 ; argon2-cffi pour le profil Argon2id exact du RFC 9106. Les primitives ne sont pas réimplémentées. Le raccord HKDF-SHA256 court suit RFC 5869 et a un test connu. L'assemblage applicatif reste nouveau et nécessite sa propre revue ; utiliser libsodium ne constitue pas un audit du conteneur.

Le format `age` a été considéré. Son profil standard mot de passe utilise scrypt et ne permet pas de le mélanger librement avec d'autres stanzas. Les besoins ET, récupération, profils Kristal et bornes applicatives imposeraient des extensions. Le dépôt ne prétend donc pas être compatible `age`, ne modifie pas sa spécification et documente honnêtement le coût de revue de son enveloppe propre.

## ADR-004 — Slots OU ; facteur ET à l'intérieur d'un slot

Mot de passe + facteur doivent tous deux participer à la dérivation cryptographique. Une entrée distincte accessible par mot de passe seul annulerait cette propriété. La récupération est intentionnellement un chemin alternatif ; son existence est affichée par `inspect`, sans révéler son secret.

## ADR-005 — Pas de faux verrou matériel

Pas de MAC, identifiant système, numéro de disque ou TPM simulé comme promesse de liaison matérielle. Interfaces de fournisseurs explicites, qualification sur matériel réel avant activation. Le fichier ne charge aucun plugin ni commande lui-même.

## ADR-006 — Validation totale et temporaires chiffrés

Aucun aperçu ni nom privé avant validation complète. Un spool chiffré répond au besoin d'accès aléatoire du parseur ZIP sans créer une copie complète en clair. Coût assumé : première lecture linéaire ; un index partiellement déchiffrable sera un autre profil si les usages le justifient.

## ADR-007 — Sources immuables et écriture transactionnelle

Pas d'édition en place. Les sources restent intactes. Nouvelle clé à chaque réemballage. Publication du fichier préparé par primitive atomique ; pas de migration, suppression, sync ou activation implicite.

## ADR-008 — Postquantique et blockchain

ML-KEM est une piste normalisée pertinente pour des secrets de longue durée. Il n'est pas activé par une simple étiquette. Un futur profil hybride devra protéger aussi les accès de récupération et être qualifié avec une bibliothèque maintenue et des vecteurs indépendants. Aucun slot inconnu n'est ignoré.

La blockchain n'aide pas les menaces principales : copie, perte de clés, fuite locale. Signature et audit indépendant appartiennent à des couches distinctes. Aucun réseau de consensus ni dépendance blockchain n'est ajouté.
