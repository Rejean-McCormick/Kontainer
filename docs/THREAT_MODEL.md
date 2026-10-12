# Modèle de menace

## Garanties et limites

| Adversaire / événement | Contrôle | Limite |
|---|---|---|
| Copie d'un fichier chiffré | Clé aléatoire, AEAD, KDF mémoire-dur | Mot de passe faible attaquable hors ligne |
| Modification/troncature/réordonnancement | Header authentifié, tags par frame, FINAL obligatoire | Un détenteur de la clé peut produire un autre contenu valide |
| Fichier ouvert malveillant | Parser strict, bornes, manifeste | Un manifeste non signé ne prouve pas l'origine |
| Origine forgée | Signature et clés de confiance extérieures | Pas de vérité factuelle ni d'autorité sémantique automatique |
| Archive hostile | STORE uniquement, chemins/tailles/comptages vérifiés | Budget CPU/disque autorisé reste consommable |
| Fuite des temporaires | Spool chiffré à clé éphémère | RAM/swap/core dumps hors protection |
| Perte d'un moyen d'accès | Slot récupération indépendant | Sans moyen prévu, aucune récupération magique |
| Ancienne version réintroduite | `expected_sha256` obtenu d'une source fiable | Le fichier seul ne sait pas quelle version est la plus récente |
| Poste compromis pendant lecture | Aucun contrôle complet dans ce dépôt | Le plaintext autorisé peut être copié |
| Appareil perdu | Réemballage, nouvelles clés pour la suite | Les anciennes copies déchiffrables ne sont pas révoquées |
| Service géré indisponible | Fournisseur qui refuse, aucun fallback implicite | Un slot de secours est un chemin alternatif volontaire |

## Actifs

Contenu, noms, métadonnées intérieures, clés de contenu, phrases secrètes, identités privées, facteurs et clés de récupération. Les empreintes logiques confidentielles doivent rester dans la partie chiffrée. Les identifiants de destinataires et la taille du fichier sont des fuites reconnues du profil v1.

## Hors du périmètre

DRM inviolable, protection contre root/administrateur, effacement garanti des SSD ou de la RAM Python, invisibilité des tailles, révocation rétroactive de plaintext, horloge fiable hors ligne, preuve de vérité, antivirus complet, sécurité des renderers ou prompt injection après déchiffrement.

Un contenu signé reste une entrée non fiable pour HTML, PDF, macros, scripts et modèles IA. Le lecteur ne rend et n'exécute rien. Les ACL/Reader Policies applicatives doivent encore précéder recherche, cache, citations et export.

## Contrôles opérationnels

Utiliser une phrase longue et unique ; le minimum de longueur n'est pas un test d'entropie. Protéger le poste et le disque système, réduire les core dumps, protéger le swap et le compte utilisateur. Garder les secrets de récupération et facteurs loin des fichiers concernés. Réduire les limites dans les services exposés et limiter leur concurrence (chaque Argon2 consomme 64 Mio). Ne pas transmettre les objets `Credentials` à un logger.

Le moteur n'a pas de rate limiter hors ligne : un attaquant peut copier le fichier et modifier le lecteur. Une prétendue limite locale de tentatives serait trompeuse. Les fournisseurs en ligne doivent gérer leurs propres limites et politiques.

## Downgrade et authenticité

L'authentification d'enveloppe protège les modifications sans clé. Un acteur autorisé au déchiffrement peut toutefois distribuer une version ouverte du même contenu signé. Les consommateurs qui exigent la confidentialité doivent fixer `require_encrypted=True` depuis une politique externe. Une signature du manifeste ne signe pas la liste des destinataires.

Une signature valide avec clé embarquée n'est que `valid-untrusted`. Les clés de confiance doivent être distribuées/authentifiées séparément. Aucun bootstrap automatique de confiance sur première ouverture n'est effectué.
