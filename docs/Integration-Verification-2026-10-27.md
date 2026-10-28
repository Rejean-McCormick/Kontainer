# Vérification des intégrations satellites — 27 octobre 2026

**Portée :** vérification statique des instantanés de code et de documentation datés du 27 octobre 2026. **Aucune qualification runtime, CI distante, publication ni autorisation de production n’est déduite de cet audit.**

## Compatibilité documentaire avec Kristal Framework

- Le snapshot du `Kristal-Framework` déclare **`11.0.0-draft.4`** pour sa sémantique v11, avec identités KQ/KP/KA/KS, dictionnaires séparés et crosswalk externe Wikidata.
- Le même contrat de release annonce séparément le **portable `kristal_state` schema `6.0`**. Il ne faut donc pas confondre la version de la sémantique v11 avec le format portable v6.
- `Kontainer` conserve son contrat de conteneur, de manifeste, de cryptographie et de lecture/écriture (baseline documentaire **1.0.0rc1**). Le fait qu'il contienne un artefact ne lui délègue pas la vérité sémantique ni l'autorité d'un RuntimeSet.
- Éléments examinés : `Kristal-Framework/VERSION`, `Kristal-Framework/contracts/release.json`, `Kristal-Framework/README.md`, `Kontainer/README.md`, `Kontainer/contracts/`, `Kontainer/src/kristal_container/`.

**Qualification restante :** tests d'interopérabilité concrets avec des artefacts v6/v11 sélectionnés et leurs empreintes; pas de compatibilité rétroactive implicite à partir de numéros de versions seuls.

## Mise à jour et preuve

Cette page décrit un état vérifié **sur fichiers**. Si le code, les contrats ou les captures de tests ont évolué depuis le snapshot, réexécuter les tests et réviser cette page avant publication.
