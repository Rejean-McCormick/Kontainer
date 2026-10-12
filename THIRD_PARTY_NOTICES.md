# Dépendances tierces

Le code source livré ne vendore pas les dépendances ; elles sont installées par le gestionnaire de paquets.

| Composant | Rôle | Licence amont à conserver selon distribution |
|---|---|---|
| PyNaCl | API libsodium | Apache-2.0 |
| libsodium | Primitives cryptographiques natives | ISC |
| argon2-cffi | API Argon2 | MIT |
| argon2-cffi-bindings | Bindings et bibliothèque Argon2 | Consulter les notices MIT / CC0 / Apache dans la distribution |
| CFFI | Interface native | MIT |
| pycparser | Parseur support CFFI | BSD |

Avant de redistribuer des wheels natives, conserver leurs notices exactes et inventorier les composants embarqués. Le tableau est un inventaire technique, pas un avis juridique.
