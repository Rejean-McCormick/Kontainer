# Contrats

Les schémas JSON Schema 2020-12 servent à l'interop et aux tests. Le parseur runtime applique des vérifications supplémentaires indispensables : canonicalisation exacte, longueur Base64 décodée, unicité des slots, paramètres KDF, noms portables, concordance des tailles, signature et authentification du flux.

Valider un schéma seul ne suffit jamais à accepter un fichier. Le schéma manifeste décrit les plafonds par défaut ; une intégration qui modifie `Limits` doit adapter ses propres contrôles. Le contrat normatif complet est `docs/FORMAT.md`, proposé au Framework.
