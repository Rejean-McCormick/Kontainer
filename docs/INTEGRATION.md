# Intégration Kristal

## État observé des pièces jointes

Le code fourni contient le Framework, l'Authoring Kit et Manager dans `Kristal-Manager(1).zip`. Le Local Kit possède `pack` et `pack-ai` qui emploient `ZIP_DEFLATED`. Sa projection `kristal.github-read-surface/1.0` énumère `path`, `size`, `sha256` préfixé `sha256:`, `ready`, `errors`, compte et volume. Manager consomme cette projection. Konfid ne stocke ni ne vérifie les mots de passe humains.

Ce dépôt est ajouté séparément. Aucun de ces dépôts n'est modifié, aucune migration canonique ni synchronisation GitHub n'est effectuée par les outils de ce dépôt.

## Contrats à adopter

| Propriétaire | Changement ciblé à intégrer |
|---|---|
| Framework | Adopter/qualifier `FORMAT.md`, les schémas et vecteurs ; conserver séparation identité/représentation |
| Authoring Kit | Ajouter un adaptateur d'export utilisant cette bibliothèque après son parcours de validation/build existant |
| Manager | Ajouter ouverture/protection/récupération, afficher l'état vérifié et empêcher l'export en clair involontaire |
| Kompiler / lecteurs | Lire via `Container`, appliquer ensuite Reader Policies avant toute vue dérivée |
| Konfid | Décisions d'accès pour un fournisseur de clés externe, pas traitement des mots de passe locaux |
| Interaction Kernel | Commandes bornées et reçus, sans assimilation à la validation sémantique |

Les schémas du dépôt ne remplacent pas les schémas des State Snapshots. Aucun recalcul des Logical Commitments n'est prétendu ici.

## Local Kit : adaptateur utilisable

Le caller obtient la projection via son interface existante :

```sh
python tools/kristal.py read-surface CHEMIN --require-ready --compact
```

Il passe l'objet décodé à l'adaptateur :

```python
from pathlib import Path
from kristal_container import Protection
from kristal_container.integration import pack_read_surface

# projection provient du Local Kit autorisé, obtenu par le caller.
pack_read_surface(Path("workspace"), Path("lecture.kristal"), projection,
                  protection=Protection(password=phrase_secrete))
```

L'adaptateur exige `ready=true` et `errors=[]`, reprend **exactement** la liste des fichiers, puis compare tailles/empreintes au snapshot emballé avant publication du résultat. Il ne lance ni build, ni shell, ni réseau. Le caller établit l'origine de la projection ; l'adaptateur ne requalifie pas son `surface_digest` ou sa sémantique.

Les blobs de `materialization_objects` ne sont pas téléchargés. Le fichier représente cette surface sélectionnée ; ce n'est pas une promesse que toutes les références externes du Kristal soient disponibles hors ligne. Pour embarquer d'autres matérialisations autorisées, le propriétaire doit définir explicitement un autre périmètre de paquet.

## Manager

Afficher séparément : ouvert/chiffré ; signature absente/inconnue/approuvée ; validation physique/validation Framework ; chemin normal/récupération. Ne jamais afficher « vérifié » sur la seule réponse `inspect`.

Une action de synchronisation d'un fichier chiffré transporte le fichier opaque. Exporter sa surface en clair, même vers un dépôt privé, exige une politique et une action explicites. Les bibliothèques tierces d'aperçu, index, logs, caches et sauvegardes doivent respecter le même périmètre de confidentialité.

Ne pas publier automatiquement l'identifiant logique confidentiel dans les index de collection. Le repo GitHub d'accueil et sa visibilité ne sont pas une assurance cryptographique.

## Lecteurs

La bibliothèque n'a pas d'ACL par membre. L'ouverture donne au processus accès à tout le paquet. Si des catégories de lecteurs ont des droits incompatibles, produire des paquets/domaines de clés séparés et conserver les relations sémantiques externes. Un champ JSON de permission n'empêche pas un détenteur de clé d'extraire les octets.

## Vérification bout en bout attendue

État construit et validé par Local Kit → empaquetage → lecture indépendante → mêmes octets d'état et mêmes références → nouvelle validation Framework avec ses outils existants. Le test de byte equality de ce dépôt n'est pas une recomputation sémantique du Framework.
