# API Python

Les chemins acceptent `pathlib.Path` (ou chemins convertibles pour l'API principale). Les exceptions attendues dérivent de `ContainerError` et portent un `code` stable.

## Création

```python
pack(source, destination,
     protection=Protection(),
     selected=None,
     signing_key=None,
     allow_sensitive=False,
     overwrite=False,
     limits=Limits(),
     expected_members=None)
```

`selected` : tuple de chemins relatifs exacts. `None` parcourt le dossier ; `()` produit un conteneur sans fichiers utilisateur. `signing_key` est une seed Ed25519 de 32 octets gérée en mémoire par l'appelant. `expected_members`, réservé aux intégrations vérifiées, contient les enregistrements `path,size,sha256` triés : le snapshot produit doit correspondre exactement avant publication.

`Protection(password=None, factor=None, factor_provider=None, recipients=(), recovery=None)` est immuable. Les secrets binaires ont 32 octets. `recipients` contient des clés publiques X25519. `factor` et `factor_provider` sont exclusifs et nécessitent un mot de passe. Les différents slots sont des accès **OU**. Une protection vide produit un fichier ouvert.

## Lecture

```python
with Container(path,
               credentials=Credentials(),
               limits=Limits(),
               trusted_signers=(),
               require_signature=False,
               require_encrypted=False,
               expected_sha256=None) as reader:
    report = reader.report
    entries = reader.list()
```

`Credentials` accepte `password`, `factor`, `factor_provider`, `identity`, `recovery`, `recipient_resolver`, `allowed_recipient_ids`. Ses secrets ne sont pas affichés par `repr`. Un objet ne doit pas être partagé entre threads ; l'application contrôle son cycle de vie.

- `read(relative_path) -> bytes` : borne `max_read_bytes`.
- `copy_to(relative_path, binary_stream)` : export en blocs, contrôle de la destination à la charge de l'appelant.
- `extract(new_directory)` : export explicite en clair, destination inexistante, sans overwrite.
- `rewrap(destination, protection=..., overwrite=False, allow_plaintext=False)` : conserve le ZIP, renouvelle la clé et le flux.
- `list() -> list[dict]` : copies des enregistrements, pas accès au manifeste mutable interne.
- `close()` : ferme ZIP et temporaire chiffré ; aucune garantie d'effacement mémoire Python.

`expected_sha256` désigne l'empreinte physique du fichier **entier**. Elle n'est utile contre le rollback que si le consommateur l'obtient d'un état extérieur fiable. Elle change après réemballage. Le `manifest_sha256` décrit les octets du manifeste, pas l'identité logique du Kristal.

## Rapports

Le rapport vérifié distingue `integrity=verified`, `signature=absent|valid-untrusted|trusted`, `mode`, compte et volume, empreinte du manifeste, identifiant du signataire et `semantic_validation=not-performed`. Le lecteur ajoute `container_sha256` ; `pack` rend le rapport du snapshot vérifié avant enveloppage.

`inspect_header(path)` ne lit que l'en-tête public et retourne `verified=False`. Il ne permet pas de décider que le fichier est sûr ou que ses slots sont authentiques.

## Erreurs

| Type | Code |
|---|---|
| `FormatError` | `invalid-format` |
| `IntegrityError` | `integrity-failed` |
| `AccessError` | `access-denied` |
| `PolicyError` | `policy-denied` |
| `LimitError` | `limit-exceeded` |
| `UnsupportedError` | `unsupported-profile` |

Une erreur d'accès peut provenir d'un mauvais secret **ou** d'une enveloppe endommagée. Ne pas promettre à l'utilisateur de distinguer ces cas. Les erreurs OS et de fournisseurs applicatifs peuvent aussi remonter ; l'appelant doit les traiter sans fallback de sécurité.
