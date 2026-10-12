# Instructions pour contributeurs et agents

- Préserver la séparation état logique / représentation physique.
- Garder les primitives dans les bibliothèques maintenues ; documenter tout protocole ou profil nouveau.
- Une protection indisponible échoue fermée. Aucun faux TPM, ID système secret, 2FA visuelle ou crypto postquantique d'étiquette.
- Ne jamais écrire de secrets réels dans ce dépôt ni les logs. Les fixtures binaires publiques ne concernent que des données synthétiques ouvertes.
- Tous les fichiers importés sont non fiables. Maintenir budgets, canonicalisation, refus des chemins, signatures et vérification complète.
- Toute modification de sécurité doit avoir un test de menace, pas seulement un test miroir de l'implémentation.
- Aucune publication, activation, migration ou synchronisation implicite dans les outils.
- Mettre à jour FORMAT, schémas, vecteurs, capacités et VALIDATION si les garanties changent.
- Rendre explicite ce qui est testé localement, testé par double, projeté ou non qualifié.
- Commandes : `python -m pytest`, `python -m ruff check src tests tools`, `python -m ruff format --check src tests tools`, `python -m build`.
