# Contribuer

Créer un environnement Python isolé et installer `-e ".[dev]"` avec `-c constraints.txt`. Lire AGENTS.md et SECURITY.md. Les changements doivent préciser problème, menace, comportement, compatibilité, tests et limites.

Le contrat v1 n'est pas extensible en ignorant des champs inconnus. Préparer les migrations de format explicitement ; ne pas changer silencieusement la signification d'une version. Ajouter un vecteur de conformité et un test adversarial pour les modifications du parser et du protocole.

Les noms de version suivent PEP 440. Une release candidate ne devient pas une release de production sur la seule base de tests locaux. Voir docs/RELEASE.md.
