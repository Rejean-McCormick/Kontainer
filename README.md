# Kristal Container

**Un dossier de données devient un fichier `.kristal` unique, non compressé, vérifiable et éventuellement chiffré.** Bibliothèque Python et CLI locales, sans serveur ni compte obligatoire.

Version livrée : **1.0.0rc1**. Le moteur local est implémenté et testé ; le protocole applicatif n'a pas reçu d'audit cryptographique indépendant. Le contrat livré est une proposition d'extension du Framework, pas une norme déjà adoptée par celui-ci.

## Ce qui fonctionne

| Capacité | État |
|---|---|
| Conteneur ouvert, ZIP64 STORE intérieur, fichiers Unicode portables | Implémenté |
| Phrase secrète, Argon2id, XChaCha20-Poly1305 `secretstream` | Implémenté |
| Mot de passe **ET** secret externe de 256 bits | Implémenté ; fichier de secret copiable, pas une authentification matérielle |
| Destinataires X25519 multiples, chacun avec son identité | Implémenté |
| Clé de récupération indépendante | Implémenté ; accès alternatif explicitement choisi |
| Signature Ed25519 et confiance externe obligatoire sur demande | Implémenté |
| Changement de protection sans changement des octets intérieurs | Implémenté |
| Temporaires chiffrés, lecture sans extraction | Implémenté |
| Adaptateur de projection Local Kit `read-surface/1.0` | Implémenté |
| Interfaces Python pour facteur externe et résolveur de clés | Implémentées et testées avec doubles de test |
| Fournisseurs natifs TPM, WebAuthn, KMS/Konfid | **Non fournis** ; intégrations à qualifier sur leur infrastructure réelle |
| Postquantique, quorum cryptographique, révocation hors ligne | Non pris en charge ; aucun faux indicateur de protection |

`kristal-container capabilities` expose ces états en JSON. Le fichier ne choisit jamais un module, un exécutable ou une URL à contacter.

## Installation

Python **3.11 à 3.14** ciblé. La validation locale de cette livraison a été effectuée sous Linux/Python 3.12 ; la matrice CI fournit les vérifications supplémentaires à exécuter.

```sh
python -m venv .venv
# Linux / macOS :
.venv/bin/python -m pip install -c constraints.txt .
.venv/bin/python -m kristal_container --help
```

Sous Windows, dans le dossier du dépôt :

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints.txt .
.\.venv\Scripts\python.exe -m kristal_container --help
```

Aucune modification de PATH permanent, association de fichier, publication ou installation système. Les commandes suivantes supposent que l'environnement virtuel est activé ; sinon, employer son chemin Python complet.

## Parcours rapide

Examiner les fichiers retenus, sans écrire :

```sh
python -m kristal_container plan examples/demo
```

Créer un Kristal ouvert :

```sh
python -m kristal_container pack examples/demo demo.kristal --mode open
python -m kristal_container verify demo.kristal
python -m kristal_container list demo.kristal
```

Créer un Kristal chiffré ; la phrase secrète est demandée dans le terminal, jamais dans les arguments :

```sh
python -m kristal_container pack examples/demo prive.kristal --mode password
python -m kristal_container verify prive.kristal --password --require-encrypted
```

L'en-tête peut être examiné sans déchiffrement, mais sa réponse est **non vérifiée** :

```sh
python -m kristal_container inspect prive.kristal
```

Les destinations doivent être extérieures au dossier source et ne pas exister, sauf `--overwrite` explicite. Un fichier protégé ne devient jamais une surface GitHub déchiffrée automatiquement.

## Récupération dès la création

```sh
python -m kristal_container keygen recovery secours.ksecret
python -m kristal_container pack examples/demo protege.kristal --mode password --recovery-key secours.ksecret
python -m kristal_container verify protege.kristal --unlock-recovery secours.ksecret
```

`secours.ksecret` est un **secret porteur en clair** : qui le possède peut ouvrir le fichier. Le déplacer dans un stockage séparé et protégé, avec sauvegarde indépendante. Ne jamais l'inclure dans le dossier emballé, le dépôt, un courriel ou l'archive du logiciel. Tester la récupération avant de compter sur elle. Aucun secret ni mot de passe de démonstration n'est livré dans ce dépôt.

Changer le mot de passe après récupération :

```sh
python -m kristal_container rewrap protege.kristal nouveau.kristal --unlock-recovery secours.ksecret --mode password --recovery-key secours.ksecret
```

La nouvelle protection remplace **tous** les accès de l'ancienne enveloppe. Les anciens fichiers restent ouvrables avec leurs anciens accès.

## Bibliothèque

```python
from pathlib import Path
from getpass import getpass
from kristal_container import Container, Credentials, Protection, pack

phrase = getpass("Phrase secrète : ")
pack(Path("mon-dossier"), Path("mon-fichier.kristal"),
     protection=Protection(password=phrase))
with Container(Path("mon-fichier.kristal"),
               credentials=Credentials(password=phrase),
               require_encrypted=True) as kristal:
    for entry in kristal.list():
        print(entry["path"], entry["size"])
```

Un lecteur valide entièrement le flux, la structure ZIP, le manifeste, les empreintes et la politique de signature demandée **avant** de fournir des noms ou du contenu. Les fichiers temporaires sont chiffrés avec une clé éphémère. La RAM, le swap et un poste compromis restent hors de cette garantie.

## Documentation

- [Utilisation et CLI](docs/USAGE.md)
- [Contrat binaire et cryptographique](docs/FORMAT.md)
- [Architecture et performances](docs/ARCHITECTURE.md)
- [Modèle de menace](docs/THREAT_MODEL.md)
- [Récupération et incidents](docs/RECOVERY.md)
- [API Python](docs/API.md)
- [Intégration de l'écosystème](docs/INTEGRATION.md)
- [Fournisseurs matériels et services de clés](docs/PROVIDERS.md)
- [Décisions techniques](docs/DECISIONS.md)
- [Tests et qualification de la livraison](docs/VALIDATION.md)
- [Références primaires](docs/REFERENCES.md)
- [Politique de sécurité](SECURITY.md)

## Développement

```sh
python -m pip install -c constraints.txt -e ".[dev]"
python -m pytest
python -m ruff check src tests tools
python -m ruff format --check src tests tools
python -m build
```

Les contraintes figent les versions runtime qualifiées, pas les outils de développement ni les empreintes de tous les paquets. Consulter `docs/RELEASE.md` avant une diffusion de production.

## Frontières

Le manifeste signe des **octets physiques**. Il ne crée ni Logical Commitment, ni autorité épistémique, ni preuve de vérité. L'empaquetage ne publie, n'active et ne synchronise rien. Les sources sont conservées ; les autres dépôts ne sont pas modifiés par cette livraison.

La licence n'est pas choisie à la place du propriétaire : voir [LICENSE](LICENSE). Le code est livré pour son utilisation et ses modifications ; aucune licence open source n'est implicitement accordée aux tiers.

## Vérification des intégrations satellites (27 octobre 2026)

Voir [le contrôle de compatibilité et les limites de qualification](docs/Integration-Verification-2026-10-27.md). Les versions et statuts externes doivent être vérifiés avant tout déploiement.

