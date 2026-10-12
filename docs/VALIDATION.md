# Validation de la livraison

Date : **11 octobre 2026**. Version : **1.0.0rc1**. Plateforme réellement exécutée : Linux x86-64, Python 3.12.14.

## Résultats observés

| Vérification | Résultat |
|---|---|
| Tests unitaires, fonctionnels et adversariaux | **62 réussis** |
| Tests génératifs Hypothesis | Inclus : entrées arbitraires bornées, seeks du spool, canonicalisation |
| Mesure coverage avec branches | **82 %**, détail machine dans VALIDATION.json |
| Recherche d’avis de vulnérabilité runtime (`pip-audit 2.10.1`) | Aucun avis connu trouvé pour les 5 distributions figées |
| Ruff lint | Réussi |
| Ruff format | Réussi |
| Build wheel et sdist | Réussi |
| Installation de la wheel dans un environnement virtuel distinct | Réussie |
| Parcours CLI du paquet installé | Création libre/chiffrée, vérification, récupération, réemballage et extraction réussis |
| Schémas JSON Schema et vecteur ouvert figé | Réussis |
| Traitement de 64 Mio synthétiques | Réussi ; mesures dans BENCHMARK.json |

La mesure de couverture n'est pas une preuve de sécurité. Les sorties numériques proviennent des commandes exécutées, pas d'une CI distante annoncée comme réussie.

## Menaces effectivement testées

Mot de passe absent/erroné ; nécessité conjointe du facteur ; récupération indépendante ; destinataire non autorisé ; signature inconnue/forgée ; politique de chiffrement ; empreinte physique attendue ; altération du header authentifié ; suppression/réordonnancement/duplication/troncature de frames ; suffixes ; paramètres KDF excessifs rejetés avant dérivation ; JSON dupliqué ; chemin absolu/traversée/ADS/noms Windows/collisions ; source liée ; secrets par noms ; fichiers non déclarés ; compression étrangère ; faux comptage du central directory ; ZIP64 avant le sentinel classique ; limites de taille ; échec d'écriture sans corruption de la cible ; contenu du temporaire chiffré ; projection Local Kit périmée ; allowlist avant callback de fournisseur.

## Preuves d'intégration et leurs limites

`pack_read_surface` est testé sur une projection synthétique conforme aux champs observés dans le Local Kit fourni. Cela prouve son contrôle des octets sélectionnés, pas un parcours graphique Manager ni une recomputation des State Commitments du Framework.

Les interfaces FactorProvider et RecipientResolver passent des tests avec doubles logiciels. Aucun test de TPM physique, présence utilisateur WebAuthn, passkey synchronisée, KMS ou Konfid déployé n'a été exécuté. Ces fournisseurs sont annoncés non supportés par le CLI.

La CI fournie cible Linux, Windows, macOS et Python 3.11–3.14. Elle n'a pas été exécutée sur GitHub dans cette livraison. Les tests ZIP64 abaissent un seuil pour vérifier les structures ; un conteneur réel de plusieurs Gio n'a pas été qualifié ici. Le test de 64 Mio ne constitue pas une promesse de performance universelle.

## Benchmark local

64 Mio de données aléatoires synthétiques, sans compression : environ **0,45 s** de création et **0,35 s** d'ouverture/vérification sur cet environnement. Taille du conteneur : **67 111 208 octets** pour **67 108 864 octets** de payload. Les performances de disque, CPU, OS, antivirus et taille du manifeste changent ces résultats.

## Statut de sécurité

Pas d'audit indépendant, certification ou homologation. Ce dépôt constitue une implémentation candidate utilisable pour intégration et revue ; il ne doit pas être renommé « certifié » ou « production critique qualifiée » sur la seule base de ces tests. Voir RELEASE.md pour les gates restantes.

## Dépendances

`DEPENDENCY_AUDIT.json` contient la recherche datée des avis connus pour PyNaCl, argon2-cffi, argon2-cffi-bindings, CFFI et pycparser, aux versions de `constraints.txt`. Cette recherche ne constitue ni un audit du code ni une analyse exhaustive des bibliothèques natives embarquées ou du système Python. Les versions de développement ne font pas partie de cette recherche.
