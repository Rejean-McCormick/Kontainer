# Contrat du fichier `.kristal` — proposition v1

Statut : profil implémenté dans `Kristal-Container 1.0.0rc1`, à adopter et maintenir normativement dans **Kristal-Framework**. Ce document décrit précisément la lecture v1 ; ajouter une protection nécessite une nouvelle spécification et des tests, jamais un repli silencieux.

## 1. Enveloppe

| Octets | Sens |
|---|---|
| 0..7 | Magic : ASCII `KRISTAL` suivi de `01` hexadécimal |
| 8..11 | Longueur de l'en-tête JSON, entier non signé 32 bits big-endian |
| suivants | En-tête UTF-8 canonique, 1 à 65 536 octets |
| suite | ZIP brut en mode ouvert ; séquence de frames authentifiées en mode chiffré |

Le JSON utilise clés triées lexicalement, séparateurs `,` et `:`, aucune espace superflue, UTF-8 sans BOM, `ensure_ascii=False`, aucun NaN/Infinity, aucun membre dupliqué. Les valeurs numériques normatives sont des entiers. Il s'agit d'un sous-ensemble défini ici, **pas d'une revendication de conformité générale RFC 8785/JCS**. Une sérialisation différente est refusée. Les champs non définis sont refusés dans les objets normatifs.

Ouvert : `{"format":"kristal.container/1","mode":"open"}`.

Chiffré : champs exacts `format`, `mode=encrypted`, `profile=xchacha20poly1305-secretstream-v1`, `id` (16 octets aléatoires), `stream` (24 octets de header secretstream), `slots` (1 à 16). Les binaires JSON utilisent Base64 RFC 4648 standard avec padding canonique.

Aucune identité logique ni nom de fichier en clair dans cet en-tête. Restent visibles : mode, algorithmes, types/nombre d'accès, identifiants SHA-256 des clés publiques destinataires et taille totale. Le profil ne fournit pas de padding.

## 2. Chiffrement du contenu

Une nouvelle clé aléatoire de **32 octets** et un nouveau flux libsodium `crypto_secretstream_xchacha20poly1305` sont générés à chaque création/réemballage chiffré. Les mots de passe ne chiffrent pas directement le contenu.

Chaque frame est précédée de sa longueur non signée 32 bits big-endian. Le plaintext est découpé en blocs de 1 048 576 octets, le dernier bloc de données pouvant être plus court. Chaque frame ajoute 17 octets libsodium. Les tags de données sont `TAG_MESSAGE=0`. Une frame vide avec `TAG_FINAL=3` est **toujours** ajoutée. Sa longueur est 17. Aucun octet ne suit cette frame ; aucun bloc de données ne suit un bloc court.

Données associées de chaque frame :

```
ASCII("kristal/stream/v1") || 00 || SHA256(magic || longueur_header_be32 || header_json)
```

Le header complet, y compris tous les accès aux clés, est donc authentifié par chaque frame. Le lecteur exige la fin authentifiée : des blocs valides partiels ne suffisent pas à accepter le conteneur.

## 3. Slots d'accès

Les slots sont des chemins **OU**. Un seul slot mot de passe (simple ou avec facteur), un seul slot récupération, aucun destinataire répété. Le writer autorise au maximum 14 destinataires, plus mot de passe et récupération. Le CLI est plus restrictif et évite les mélanges involontaires de destinataires et mot de passe ; l'API permet leur combinaison explicite.

### Mot de passe

`type=password`, `kdf`, `salt` (16 octets), `nonce` (24), `wrapped` (48).

KDF exact : `name=argon2id`, `version=19`, `memory_kib=65536`, `iterations=3`, `parallelism=4`, sortie 32 octets. La phrase est encodée UTF-8, sans normalisation ni troncature. Création : 15 à 1024 caractères, au plus 4096 octets. Les variantes de coûts sont refusées avant calcul ; elles nécessiteraient un autre profil.

Dériver `D = Argon2id(password, salt)`, puis `KEK = HKDF-SHA256(D, salt=container_id, info="kristal/password/v1", L=32)`.

Chiffrer la clé de contenu avec XChaCha20-Poly1305, nonce aléatoire, AAD :

```
ASCII("kristal/keyslot/v1") || 00 || container_id || canonical(slot_sans_wrapped)
```

### Mot de passe ET facteur

Mêmes champs, `type=password-factor`. Dériver `D` comme ci-dessus, puis `KEK = HKDF-SHA256(D || facteur_32_octets, salt=container_id, info="kristal/password-factor/v1", L=32)`.

Le facteur provient d'un secret aléatoire ou d'un `FactorProvider` explicitement fourni par l'application. Un simple fichier de secret est copiable et ne prouve pas la présence d'un matériel. Le type ne certifie aucune assurance MFA ; celle-ci appartient au fournisseur qualifié.

### Récupération

`type=recovery`, `nonce` (24), `wrapped` (48). Secret indépendant aléatoire de 32 octets. `KEK = HKDF-SHA256(secret, salt=container_id, info="kristal/recovery/v1", L=32)`, puis même wrapping AEAD. Le secret n'est jamais enregistré dans le conteneur.

### Destinataire X25519

`type=x25519`, `key_id=SHA256(public_key_32_octets)` en hexadécimal minuscule, `wrapped` (96 octets).

`wrapped = libsodium SealedBox(public_key, container_id || content_key)`. SealedBox utilise la construction standard libsodium X25519/XSalsa20-Poly1305 ; l'algorithme du slot est donc distinct de celui du flux. Vérifier le container_id après ouverture. Une sealed box n'authentifie pas l'expéditeur : les signatures ont une autre fonction.

### HKDF

RFC 5869 SHA-256 : `PRK=HMAC(salt, IKM)`, sortie unique `HMAC(PRK, info || 01)` (32 octets). Ne jamais réutiliser les labels entre domaines.

## 4. ZIP intérieur

Profil volontairement plus strict qu'un ZIP générique :

- uniquement fichiers réguliers, `STORE`, pas de répertoires explicites ; aucun lien, exécutable automatique ou flux NTFS ;
- noms relatifs UTF-8 NFC, `/`, au plus 1024 octets ; chaque composant au plus 240 octets ;
- refus de `..`, `.`, composants vides, antislash, caractères de contrôle/format, `:*?"<>|`, noms réservés Windows et suffixes point/espace ;
- aucun doublon, alias de casse ou conflit fichier/répertoire ; namespace `_kristal` réservé ;
- ordre lexicographique des noms utilisateur ; `_kristal/manifest.json` en dernier ;
- horodatage fixe 1980-01-01 00:00:00 ; système créateur Unix (3), attribut externe `0o100600 << 16` ;
- en-tête local ZIP64 version 45 pour chaque membre, flag descriptor (8), flag UTF-8 si nécessaire ; CRC local nul, tailles locales `0xffffffff` ;
- extra local exact : identifiant 1, longueur 16, deux tailles nulles de 64 bits ;
- descriptor signé `PK\x07\x08`, CRC32, taille compressée et réelle 64 bits little-endian ;
- aucun trou, préfixe, recouvrement, commentaire ou suffixe ; aucun extra autre que ZIP64 ;
- central directory et EOCD/ZIP64 EOCD cohérents et bornés avant allocation du parseur.

CRC32 n'est pas une protection cryptographique. Les empreintes SHA-256 du manifeste couvrent les fichiers ; le flux authentifié protège le paquet chiffré. Les archives ZIP ordinaires doivent être converties par `pack` depuis un dossier autorisé, pas acceptées directement.

## 5. Manifeste et signature

Manifeste canonique : `format=kristal.container-manifest/1`, `files=[{path,size,sha256}, ...]`, `signature` optionnelle. Tailles entières positives ou nulles, SHA-256 hexadécimal minuscule. Chaque fichier hors manifeste apparaît exactement une fois ; aucune donnée supplémentaire n'est ignorée.

Signature : champs exacts `algorithm=ed25519`, `public_key` (32 octets), `value` (64 octets).

```
signature = Ed25519.sign(
  ASCII("kristal/container-manifest/1") || 00 || canonical(manifeste_sans_signature)
)
```

La clé embarquée permet de vérifier la cohérence cryptographique ; elle n'établit **pas** sa propre confiance. L'application fournit ses clés de confiance hors du fichier. `require_signature=True` sans clé de confiance refuse tout fichier. Fournir des clés de confiance implique une signature correspondante obligatoire.

La signature engage les chemins, tailles et contenus via leurs empreintes, pas la politique d'ouverture, le ZIP physique exact ni un Logical Commitment du Framework. Une politique locale `require_encrypted` et une autorisation de distribution restent nécessaires. Une clé de signature approuvée n'est pas une autorisation d'exécuter le contenu.

## 6. Limites par défaut

10 000 fichiers, 8 Gio par fichier, 16 Gio de contenu, manifeste 8 Mio, central directory 16 Mio, lecture directe `read()` 16 Mio. Le calcul des temporaires ajoute un budget de structure borné. `copy_to()` traite les gros fichiers par blocs. L'API `Limits` peut modifier ces limites positives ; augmenter une limite augmente le budget de ressources accordé à un import hostile.

## 7. Fichiers de clés

Format canonique `kristal.key/1`. `kind` distingue `identity`, `signing`, `recipient`, `verify`, `recovery`, `factor`. Matériel brut 32 octets.

Les clés privées identité/signature sont obligatoirement chiffrées sur disque : même Argon2id, puis `_password_key` avec l'identifiant de domaine fixe `b"kristal-key-v1\x00\x00"`, XChaCha20-Poly1305, AAD `b"kristal/keyfile/v1\x00" || canonical(objet_sans_encrypted)`. Champs : format, kind, kdf, salt, nonce, encrypted. Les secrets de secours/facteur et clés publiques utilisent `data` Base64 ; les premiers doivent être stockés séparément et protégés.

La confidentialité d'un fichier de clés ne garantit pas une clé matérielle non exportable.
