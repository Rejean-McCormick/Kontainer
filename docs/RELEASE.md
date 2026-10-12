# Qualification et diffusion

## Vérifications de la livraison

1. Environnement isolé, contraintes runtime, tests et lint.
2. Build wheel + sdist ; installation de la wheel et parcours CLI avec données synthétiques.
3. Vérification des schémas/vecteurs et absence de secrets réels dans l'archive.
4. Rapport VALIDATION daté qui distingue résultats observés et étapes non exécutées.
5. Archive source et empreintes SHA-256. Une empreinte fournie avec le paquet ne remplace pas une signature de diffusion par une identité de confiance.

## Avant production sensible

- Revue cryptographique indépendante de l'enveloppe et de la composition des accès.
- CI réellement exécutée sur les versions Python et OS supportés, notamment Windows/NTFS et ses ACL.
- Tests de gros volumes/ZIP64 sur les volumes cibles, interruption du processus et saturation disque.
- Vérification des dépendances/CVE à la date de diffusion ; génération d'un lock avec hashes adapté aux plateformes et d'un SBOM complet si distribution binaire.
- Adoption explicite du contrat par Framework et tests interop indépendants.
- Exercice de récupération avec les vrais détenteurs et moyens de secours.
- Pour un fournisseur matériel/géré, qualification spécifique de PROVIDERS.md.
- Choix de licence et canal privé de signalement par le propriétaire avant diffusion publique.

Les workflows CI ne publient aucun package ni fichier de production. La création d'un dépôt GitHub, le push, les releases et l'activation restent des opérations distinctes.

## Versions et migration

La release candidate fige un candidat de format v1 pour revue. Tout changement incompatible avant adoption doit être signalé et disposer d'un outil explicite de conversion avec vérification. Une migration ne doit pas remplacer silencieusement des fichiers existants ou perdre des moyens de récupération.

## Retour arrière

Le moteur écrit de nouveaux fichiers et ne modifie pas les sources par défaut. Revenir à l'ancienne version du logiciel et aux copies antérieures validées. Après un `--overwrite` explicite, la restauration dépend de la sauvegarde du propriétaire : l'atomicité n'est pas une sauvegarde historique.
