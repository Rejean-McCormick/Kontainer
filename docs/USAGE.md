# Utilisation

Toutes les commandes terminent par un objet JSON. Les secrets sont saisis par `getpass`, ou par des descripteurs explicites pour l'automatisation. Aucun argument `--password valeur` ni variable d'environnement contenant un mot de passe n'est prévu. `--password` est uniquement un indicateur de saisie interactive.

## Commandes

| Commande | Action |
|---|---|
| `capabilities` | Versions, fonctions réellement supportées, absence d'audit indépendant |
| `plan SOURCE` | Liste des fichiers sélectionnés et tailles ; aucune écriture |
| `keygen TYPE OUTPUT` | Génération d'un secret ou d'une paire de clés |
| `pack SOURCE OUTPUT --mode MODE` | Création d'un fichier, après validation du snapshot |
| `inspect FILE` | En-tête public non vérifié |
| `verify FILE` | Vérification complète, y compris déchiffrement si nécessaire |
| `list FILE` | Liste des membres uniquement après vérification complète |
| `export FILE MEMBER OUTPUT --allow-plaintext` | Export explicite d'un seul fichier en clair |
| `extract FILE DIRECTORY --allow-plaintext` | Export complet dans un nouveau répertoire |
| `rewrap FILE OUTPUT --mode MODE` | Nouvelle protection du même ZIP intérieur |

Codes de sortie : 0 succès ; 2 erreur de format/intégrité/accès/politique ; 3 erreur d'environnement/opération ; 130 annulation. Les erreurs de parsing argparse utilisent aussi 2 mais sont affichées par argparse en texte. Le CLI n'affiche pas de traceback ni de chemin sensible pour les erreurs OS courantes.

## Sélection des données

Sans `--include`, les fichiers réguliers du dossier sont sélectionnés récursivement. Le moteur **refuse**, au lieu d'omettre silencieusement, les chemins de développement et secrets courants (`.git`, `.env*`, clés privées, `.venv`, etc.). Cette détection par nom n'est pas un scanner exhaustif de secrets.

```sh
python -m kristal_container plan mon-dossier --include state/snapshot.json --include docs/README.md
python -m kristal_container pack mon-dossier sortie.kristal --mode open --include state/snapshot.json --include docs/README.md
```

Chaque `--include` désigne un fichier exact, pas un glob ni un répertoire. L'API Local Kit est préférable pour une projection officielle. `--allow-sensitive` permet explicitement des noms bloqués, sans désactiver les contrôles de chemins, liens, limites ou intégrité.

Les dossiers vides, permissions originales, ACL, timestamps et attributs étendus ne sont pas préservés. Le format est un conteneur de **contenus portables**, pas une image de sauvegarde du filesystem. Aucun blob externe n'est téléchargé automatiquement.

## Mot de passe et second secret

```sh
python -m kristal_container keygen factor facteur.ksecret
python -m kristal_container keygen recovery secours.ksecret
python -m kristal_container pack mon-dossier protege.kristal --mode password-factor --factor-key facteur.ksecret --recovery-key secours.ksecret
python -m kristal_container verify protege.kristal --password --unlock-factor facteur.ksecret
```

C'est une exigence cryptographique de deux secrets pour l'accès normal. Un fichier facteur copiable n'est pas une clé FIDO/TPM, et ne doit pas être annoncé comme un facteur matériel. Le secret de récupération constitue un accès alternatif qui peut ouvrir seul.

## Destinataires

```sh
python -m kristal_container keygen identity alice.kkey --public alice-public.json
python -m kristal_container keygen identity bob.kkey --public bob-public.json
python -m kristal_container pack mon-dossier partage.kristal --mode recipient --recipient alice-public.json --recipient bob-public.json
python -m kristal_container verify partage.kristal --identity alice.kkey
```

Les identités privées sont protégées par un mot de passe de fichier de clés. Chacun des destinataires peut ouvrir seul. Les clés publiques doivent être authentifiées par un canal extérieur. X25519 n'est pas un profil postquantique.

## Signatures

```sh
python -m kristal_container keygen signing auteur.kkey --public auteur-public.json
python -m kristal_container pack mon-dossier signe.kristal --mode open --signing-key auteur.kkey
python -m kristal_container verify signe.kristal --trust auteur-public.json
```

Fournir `--trust` impose une signature de cette liste de confiance. Sans `--trust`, une signature embarquée n'est pas approuvée automatiquement. `--require-signature` sans clé de confiance ne permet aucun signataire et échoue volontairement.

## Réemballage et perte d'accès

```sh
python -m kristal_container rewrap ancien.kristal nouveau.kristal --password --mode password
```

Deux saisies : ancien mot de passe puis nouveau confirmé. `--new-password-fd` distingue la nouvelle phrase dans un script. Les slots de récupération/destinataire existants ne sont **pas** conservés implicitement : les fournir explicitement dans la nouvelle protection.

Retirer le chiffrement exige `--mode open --allow-plaintext`. Écraser un fichier exige `--overwrite`. Ces options sont indépendantes. Les anciennes copies restent accessibles : voir RECOVERY.md.

## Automatisation et fenêtres Windows

Utiliser la bibliothèque directement dans Manager pour ses boîtes de dialogue et ses processus masqués, plutôt que d'injecter un mot de passe dans une ligne de commande. Pour un processus enfant, utiliser `subprocess` avec liste d'arguments, `shell=False`, des pipes hérités explicitement pour les mots de passe, et lire le code de sortie avant le JSON. Les mécanismes de descripteurs hérités diffèrent entre POSIX et Windows ; privilégier l'API Python dans le Manager Windows.

Les descripteurs doivent contenir UTF-8 et atteindre EOF. Une seule fin de ligne finale LF ou CRLF est retirée pour l'automatisation. Les mots de passe ne sont jamais tronqués silencieusement.

Il n'y a pas de lecteur graphique distinct dans ce dépôt : Manager/Konstellation restent propriétaires de l'interface. Aucune association de l'extension `.kristal` n'est installée.
