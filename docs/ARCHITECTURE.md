# Architecture et performances

## Propriété des responsabilités

Le Framework conserve les contrats et la sémantique. Ce dépôt implémente un profil physique. Le Local Kit construit les états ; Manager orchestre l'expérience et le transport ; les lecteurs consomment les octets autorisés. Konfid décide des droits dans les parcours gérés. Aucun de ces rôles n'est fusionné ici.

| Module | Responsabilité |
|---|---|
| `api.py` | Transactions de paquet, lecture vérifiée, extraction explicite, réemballage |
| `archive.py` | Sélection, ZIP64 strict, manifeste, signatures |
| `crypto.py` | Enveloppe, slots, KDF, AEAD et secretstream |
| `staging.py` | Stockage temporaire chiffré, accès aléatoire en lecture |
| `filesystem.py` | Fichiers réguliers, refus des liens, publication atomique |
| `keys.py` | Clés typées, chiffrement des clés privées |
| `integration.py` | Projection Local Kit, sans duplication du moteur sémantique |
| `providers.py` | Interfaces de fournisseurs injectés par l'application |
| `cli.py` | Arguments sûrs et résultats JSON |

## Écriture

Inventorier → lire les fichiers par blocs → ZIP STORE dans le temporaire chiffré → vérifier structure et empreintes → envelopper → fsync du nouveau fichier → publier atomiquement.

La création refuse une destination dans la source. Elle ne supprime ni ne modifie les sources. Elle vérifie leur identité et métadonnées avant/après lecture et compare l'inventaire final. Une source modifiée concurremment doit être stabilisée ou issue d'un snapshot système ; cette vérification ne remplace pas un snapshot de filesystem face à un adversaire local actif.

Le mode ouvert est déterministe pour les mêmes chemins/octets et la même signature. Les fichiers chiffrés sont volontairement différents à chaque écriture. Le `rewrap` conserve exactement le ZIP intérieur, ses signatures et les états sémantiques qu'il transporte.

## Lecture

Copier/déchiffrer vers le spool chiffré → vérifier fin authentifiée → précontrôler le central directory → vérifier tous les membres et le manifeste → vérifier la politique de signature → exposer une vue en lecture seule.

Le fichier source peut ensuite être fermé : le lecteur consulte son snapshot privé, pas une nouvelle lecture du chemin initial. `inspect` lit seulement des assertions publiques non authentifiées et le signale explicitement.

## Temporaires

`EncryptedSpool` écrit des blocs de 1 Mio avec XChaCha20-Poly1305, clé aléatoire éphémère 32 octets, nonce `random16 || index_be64`, AAD de domaine et index. Chaque bloc n'est écrit qu'une fois. Le dernier est court. Position et taille attendues viennent de la mémoire de confiance. Le stockage chiffré permet les seeks nécessaires au ZIP sans déverser de plaintext sur disque.

Un bloc déchiffré est mis en cache ; la RAM dépend principalement de quelques blocs, du manifeste et des métadonnées ZIP, plus **64 Mio** pendant Argon2id. Python et les bibliothèques produisent des copies mémoire ; aucun effacement garanti des secrets n'est revendiqué. Le fichier temporaire est supprimé/fermé normalement, mais peut rester chiffré après panne.

## Coût et choix assumés

- Création : plusieurs passes locales de lecture/vérification ; coût O(taille totale), pas chargement complet en RAM.
- Ouverture : vérification complète O(taille totale), avant la première donnée ; ensuite accès aux membres depuis le spool.
- Réemballage : nouvelle clé de contenu, nouveau chiffrement intégral. Pas de rotation d'en-tête seule fragile.
- STORE : aucune compression, économie de CPU et absence de bombes de décompression acceptées ; petite expansion de structure et d'authentification.
- Pas de modification en place ; chaque résultat est un nouveau snapshot.
- Pas de promesse de millisecondes pour des centaines de Gio. Un futur profil d'accès partiel chiffré nécessite une conception distincte et une revue de sécurité.

## Atomicité et OS

Les fichiers sont préparés dans le parent de destination, fsync avant publication. Sans overwrite, la publication utilise un hardlink atomique qui échoue si la cible existe. Les filesystems sans hardlinks ne bénéficient pas d'un fallback racy : l'opération échoue. `--overwrite` utilise `os.replace`. Le parent est fsync sur POSIX.

Les parents de sources/destinations doivent appartenir à une zone de confiance. Refus des symlinks et reparse points connus, mais aucune protection absolue contre un administrateur ou un processus du même utilisateur qui remplace des répertoires en course.

L'extraction est un export explicite en clair dans un **nouveau** répertoire. Elle nettoie sur erreur ordinaire, mais une interruption brutale peut laisser des fichiers partiels. Elle n'est pas une transaction de répertoire atomique. Sous Windows, modes POSIX 0600/0700 ne remplacent pas une DACL : configurer un profil utilisateur/volume protégé.
