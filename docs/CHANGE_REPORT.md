# Rapport de livraison

## Dépôt

Nouveau dépôt autonome `Kristal-Container`, version 1.0.0rc1. Bibliothèque Python, CLI, documentation française, schémas, tests, outils de vérification, CI, vecteur de conformité et paquet installable.

## Fichiers et responsabilités

- `src/kristal_container/` : implémentation du moteur, clés, parser, stockage et API.
- `tests/` : cas fonctionnels/adversariaux/génératifs, contrat Local Kit et fournisseurs.
- `contracts/` et `docs/FORMAT.md` : proposition de contrat à adopter par Framework.
- `docs/` : utilisation, API, architecture, récupération, menaces, providers, décisions, références et preuves.
- `.github/` : tests multiplateformes et mises à jour proposées de dépendances, sans publication.
- `examples/` : uniquement données synthétiques et conteneur ouvert vérifiable.
- `tools/` : gates locales et benchmark opt-in.

Aucun fichier des archives sources n'est modifié. Aucun workspace canonique, dépôt externe, compte, serveur ou appareil n'est activé/configuré.

## Contrats nouveaux

`kristal.container/1`, `kristal.container-manifest/1`, `kristal.key/1`, rapports de vérification/capacités et interfaces Python de fournisseurs. Le seul contrat existant consommé est la projection `kristal.github-read-surface/1.0`. Aucun contrat sémantique n'est redéfini.

## Retour arrière

La création normale écrit un nouveau fichier et laisse le dossier source intact. Le paquet logiciel peut être retiré de son environnement virtuel. Un overwrite explicitement demandé nécessite une sauvegarde antérieure pour retrouver cette version. La suppression du logiciel n'efface pas les secrets/fichiers conservés par le propriétaire.

## À intégrer séparément

Adoption du contrat par Framework ; commandes d'export Authoring Kit ; dialogues Manager ; API de lecture Kompiler/Konstellation ; fournisseurs matériel/organisation selon le profil de déploiement. Aucun de ces changements inter-dépôts n'est prétendu déjà installé.
