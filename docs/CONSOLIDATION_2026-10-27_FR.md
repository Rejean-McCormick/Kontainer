# Kontainer — rapport de consolidation (27 octobre 2026)

## Décision

**Un seul dépôt source canonique : `Kontainer` (`kristal-container` v1.0.0rc1).**
Les deux ZIP examinés ne sont **pas** deux moteurs ou deux générations du produit. Ils ont **58 fichiers communs, strictement identiques octet pour octet**. Aucune fusion de code n'est nécessaire.

### Apport de chaque archive

- `znapshot_Kontainer_10271324.zip` : 61 fichiers source, dont `GitSink.bat`, `ZmartZnap.pyw` et `SNAPSHOT_INDEX.txt`, exclusifs à cette archive.
- `kontainer.zip` : mêmes 58 fichiers communs, plus les deux distributions Python de `dist/` (`.whl` et `.tar.gz`).
- Le ZIP consolidé contient la **réunion exacte des 63 fichiers d'origine**, plus le présent rapport et un manifeste de leurs empreintes. Aucun fichier métier initial n'a été modifié.

### Contrôles effectués durant cette consolidation

- Intégrité CRC des deux ZIP d'entrée et comparaison SHA-256 fichier par fichier : **58/58 fichiers communs identiques**.
- **13 modules Python** de la wheel identiques aux `src/kristal_container/*.py` du snapshot.
- Fichiers du sdist en commun avec les sources : octets identiques (les métadonnées générées ne sont pas des modifications du moteur).
- Wheel : **18/18 empreintes** du fichier `RECORD` vérifiées.
- Analyse syntaxique Python de **21 fichiers** (source, tests, outils), **7 fichiers JSON** valides et **2 schémas JSON Schema** valides.
- ZIP consolidé réextrait et vérifié selon le manifeste SHA-256.

### Limites de vérification

**Les tests fonctionnels n'ont pas été réexécutés dans la session de consolidation.** PyNaCl et les dépendances dev nécessaires ne sont pas disponibles dans l'environnement local, et le téléchargement PyPI échoue. La documentation historique `docs/VALIDATION.md` rapporte **62 tests réussis le 11 octobre 2026** dans son propre environnement ; cette preuve historique n'est pas un nouveau résultat de test.

Le format, la cryptographie et le protocole restent une **release candidate sans audit cryptographique indépendant**. Aucune affirmation de qualification Windows, TPM/WebAuthn/KMS, production sensible ou certification Framework n'est ajoutée.

## Organisation conservée

```text
Kontainer/
  src/kristal_container/  ← unique code de la bibliothèque
  tests/                  ← tests existants, inchangés
  contracts/              ← mêmes schémas, inchangés
  docs/                   ← documentation originale + ce rapport
  dist/                   ← wheel et sdist déjà fournis, non recréés
  examples/               ← exemples originaux
  .github/                ← CI originale
  CONSOLIDATION_SHA256.json
```

`dist/` est déjà dans `.gitignore` et ne doit pas servir de deuxième repository. Les paquets déjà fournis sont conservés **comme artefacts distribuables**, pas comme deuxième source de vérité. `SNAPSHOT_INDEX.txt` conserve son état de snapshot d'origine ; pour cette consolidation, utiliser `CONSOLIDATION_SHA256.json`.

## Installation locale prudente

1. Sauvegarder **les deux dossiers existants** et leurs fichiers de configuration avant toute suppression ou remplacement.
2. Choisir **un seul** dossier de code canonique (ex. `C:\mycode\Kontainer`). Préserver le dossier `.git` de la branche active si présent, et comparer les éventuelles modifications locales non incluses dans les ZIP.
3. Extraire le ZIP consolidé dans ce dépôt de code (pas dans un espace de données `.kristal`). Ne pas remplacer ni déplacer des conteneurs, clés, secrets ou contenus privés.
4. Pour une validation de fonctionnement, créer un environnement virtuel et exécuter `python tools/check.py` **avec les dépendances de `constraints.txt` installées**.
5. Après comparaison et validation sous Windows, archiver éventuellement l'ancien dossier redondant. **Ne pas le supprimer automatiquement**, car ses données locales ne sont pas contenues dans les ZIP.

## Ce qui n'a pas changé

API, CLI, formats d'enveloppe, chiffrement, signature, récupération, adapters, schémas, tests, workflow et version `1.0.0rc1`. Aucune donnée, dépôt GitHub, fichier de clé ou conteneur réel n'est modifié.
