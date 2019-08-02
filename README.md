# image_crawler_app

## Sujet

Developper un workflow asynchrone de distribution de taches en python3 sous docker.

Objectifs:
- Recuperer les images accessibles par les urls contenues dans le fichier urls.txt.
- Developper une tache qui calculera la MD5 de l'image
- Developper une tache qui transformera l'image en niveau de gris avec le calcul suivant: (R + G + B) / 3
- Developper une tache qui recuperera les outputs des deux precedents workers. Il devra egalement inserer dans une base
de donnees MongoDB, les informations (md5, l'image en niveau de gris, la hauteur et la largeur de l'image, la date d'insertion).
- Developper une api en Flask pour visualiser les images stockees dans MongoDB via l'url http://localhost:5000/image/<MD5>
- Developper une api en Flask de monitoring via l'url http://localhost:5000/monitoring. Cette api devra retourner un
histogramme decrivant le nombre d'images traitees avec succes ou erreur par interval d'une minute. (Prevoir une collection dans MongoDB pour recuperer ces informations)


Notes:
- Certaines URLs retournent une erreur
- Il ne doit pas y avoir de doublons d'image dans la base MongoDB (unicite du MD5)
- Les technologies autres que celles citees sont libres
- Le travail sera rendu sur un repo git public


## Notes

Ceci est mon premier projet réalisé avec Docker, c'était donc une bonne occasion d'apprendre son fonctionnement et de l'appliquer avec ce simple exemple.

Pour répondre au problème j'ai créé plusieurs services, chacun construit sur un container:

- *api*: Le service api est une Flask API, qui me permet de créer des routes pour répondre aux besoins du problèmes, avec plusieurs endpoints, que je détaillerai ensuite.

- *image_crawler*: Ce service est celui qui permet, à partir d'une liste d'URL, de les parcourir une par une, télécharger le contenu et le stocker dans un dossier temporaire.

- *image_processor*: Ce service est celui va récupérer les fichiers dans le dossier temporaire (des images) les traiter et insérer le contenu nécessaire dans une base mongodb.

- *mongodb*: La base de donnée utilisée pour le projet, qui permet de sauvegarder les informations liées à l'image, les images ainsi que des logs concernant l'insertion des images. Plus de détails plus tard.


L'ensemble des service est orchestré grâce au fichier _docker_compose_ qui permet de déployer l'ensemble des containers.

## Crawling d'image

> - Recuperer les images accessibles par les urls contenues dans le fichier urls.txt.

J'ai donc réalisé un premier service, *image_crawler*, dont le but est donc de la récupération des images sur les liens fournis dans le fichier *urls.txt*. Le process est relativement simple, il télécharge l'image via l'url, créé un id unique (uuid), et socke l'image id.png dans un dossier temporaire partagé entre les containers grâce aux *volumes*. Si jamais la requête n'aboutit pas (peu importe la raison), le lien est abandonné et un log est envoyé dans la collection **db.insert_logs** décrite plus tard, avec le timestamp actuel.

Il aurait été possible de faire une gestion d'erreur plus solide, faire du retry sur les liens sur lesquels la requête n'a pas aboutis ou logger plus en détail les erreurs.

## Processing d'image

> - Developper une tache qui calculera la MD5 de l'image
> - Developper une tache qui transformera l'image en niveau de gris avec le calcul suivant: (R + G + B) / 3
> - Developper une tache qui recuperera les outputs des deux precedents workers. Il devra egalement inserer dans une base de donnees MongoDB, les informations (md5, l'image en niveau de gris, la hauteur et la largeur de l'image, la date d'insertion).

Ce second worker, a pour but de process les images se trouvant dans ce dossier temporaire dans lequel le premier worker dépose ses images.
Il fonctionne grâce à une librairie python appellée _watchdog_ dont le but est de monitorer des "file system events". Il permet en gros de déclencher des process lorsqu'un évènement dans un dossier occure, comme par exemple la création d'un nouveau fichier.
Une fois le trigger d'un nouveau fichier:
- il load ce fichier
- il le supprime directement pour éviter les conflits avec d'autres workers potentiellement.
- processe l'image (détaillé ensuite).
- insert le résultat du processing dans la base de données.

Il était question de process l'image sur plusieurs workers. Faute de temps je n'ai pas implementé ces fonctionnalités et me suis contenté d'un worker pour crawl et un worker pour process, simplifiant le problème.

Le process de l'image est plutôt simple:
- récupération des metadata de l'image brute (md5, width, height)
- transformation de l'image en niveau de grix

Le md5 est donc bien celui de l'image en RGB et non celui en niveau de grix.
Pour le niveau de grix, je n'ai pas pris le temps de respecter la condition 1/3 1/3 1/3 pour les 3 niveaux. La librairie PIL de python que j'ai commencé à utiliser ne permet pas simplement de set des custom ratios, à prioris.

L'insertion de l'image et de ses metadata est décrite plus tard avec les détails quant à la gestion de la base de données.

## Gestion de la base de données

### db.images

>Il devra egalement inserer dans une base
de donnees MongoDB, les informations (md5, l'image en niveau de gris, la hauteur et la largeur de l'image, la date d'insertion)

Il est question de stocker des images dans une mongodb, pour cela j'ai utilisé **gridfs** qui est une particularité de MongoDB pour stocker des fichiers. Chaque fichier stocké est décomposé en chunks, il est normalement utilisé pour stocker des fichiers de grande taille mais j'ai trouvé intéressant de l'utiliser pour la pratique. Gridfs utilise deux collections, une pour stocker les metadata une pour stocker les chunks. Il existe un wrapper en python, qui s'instantie en surcouche d'un agent pymongo, afin de manipuler ces collections. Ainsi, en insérant une image dans le gridfs, on récupère l'id (la référence de l'image dans gridfs), que l'on peut stocker dans notre collection de metadata que l'on a créé: **db.images**.

Cette collection nous sert à stocker les informations calculées par l'*image_processor*.

L'insertion d'image se fait de la sorte:
- Transformation en bytes de l'image.
- Insertion de l'image en bytes dans le gridfs et récupération de l'id associé.
- Ajout de cet id, renomé *image_id* dans les metadata.
- Sauvegarde des metadatas dans la table.

> - Il ne doit pas y avoir de doublons d'image dans la base MongoDB (unicite du MD5)

Sur MongoDB, l'unicité des documents dans une collection se fait sur le champ _"\_id"_. Pour chaque image, nous générons ses metadata (hauteur, largeur, image) ainsi que son md5. Ce md5 est unique pour chaque image et nous permet de différencier les images et ainsi les stocker avec un id unique. J'ai donc remplis le champ _"\_id"_ par le md5 lors de l'insertion de la collection dans la table. Nous stockons aussi la date d'insertion (à titre d'info uniquement). Ainsi le schéma d'une collection dans la base est le suivant:

```py
{
  "_id": "md5 de notre image",
  "image_id": "id de référence de notre image en gray scale dans le gridfs",
  "insert_time": "le timestamp de l'insertion",
  "width": "la largeur de l'image",
  "height": "la hauteur de l'image"  
}
```

### db.insert_logs

> - Developper une api en Flask de monitoring via l'url http://localhost:5000/monitoring. Cette api devra retourner un
histogramme decrivant le nombre d'images traitees avec succes ou erreur par interval d'une minute. (Prevoir une collection dans MongoDB pour recuperer ces informations)

Afin de stocker les logs d'insertion, il est nécessaire de créer une deuxième collection, que j'ai appelé **db.insert_logs**.

Schéma de la collection:
```py
{
  "_id": "id unique du document automatiquement généré",
  "interval": "la datetime de la minute concernée",
  "fail": "le nombre d'insertions dont le statut est fail",
  "success": "le nombre d'insertions dont le statut est success",
}
```

Le but de cette collection est de stocker, sur des intervalles d'1 minute, le nombre de succès et le nombre d'échecs dans le process.

Les raisons d'échecs sont les suivantes:
- *image_crawler*: la requête n'a pas pu aboutir.
- *image_processor*: l'image existe déjà.

Ainsi lorsque ces échecs occurent, on récupère le timestamp actuel, que l'on ramène à la minute inférieure, et l'on update le document de l'intervalle associé dans la table. On incrémente de 1 le compteur "fail". Si jamais la collection pour l'intervalle associé n'existe pas on créé un document vierge avec fail=0 et success=0. Cela peut créer des conflits lorsque l'on a plusieurs instances (par exemple 2) voulant écrire au même moment dans la collection un document vierge (ils vont tous les deux créé un document vierge avec le même intervalle). Je n'ai pas eu l'occasion de corriger ce potentiel soucis.

Le succès arrive dans un seul cas:
- *image_processor*: l'image a bien été insérée dans la base de données.

Dans ce cas là, comme pour un échec, on update un document existant (ou on en créé un nouveau si non existant) en incrémentant le compteur "success" de 1.

## L'API

> - Developper une api en Flask pour visualiser les images stockees dans MongoDB via l'url http://localhost:5000/image/<MD5>

Simplement, j'ai créé un endpoint sur l'API qui permet via la base de données de récupérer l'image en fonction de son md5, le retransformer en image et le render, en utilisant le module pour interférer avec la base de données décrit plus bas. Si le md5 ne correspond à aucune image on affiche rien.

> - Developper une api en Flask de monitoring via l'url http://localhost:5000/monitoring. Cette api devra retourner un
histogramme decrivant le nombre d'images traitees avec succes ou erreur par interval d'une minute. (Prevoir une collection dans MongoDB pour recuperer ces informations)

Pour ce point j'ai bien, comme décrit plus haut, créé et alimenter cette collection, mais n'ai pas eu le temps de tester quelquechose pour afficher un histogramme, même si les données de la collection sont suffisantes. Pour chaque intervalle sur lequel on a travaillé on a bien le nombre d'images traitées avec succès ou erreur.

## Tools: MongoAgent

J'ai développé un petit module *MongoAgent* pour interférer avec la base mongodb, qui hérite de la classe *MongoClient* de *pymongo*, qui permet de réaliser facilement toutes les fonctions liées à l'insertion et récupération de collections dans la base mongo.

Il permet de faire toutes les fonctions de get nécessaire dans les différents process et les différentes insertions. Il aurait peut être été plus rigoureux d'avoir un agent par process afin d'éviter que le librairie d'image utilisée pour load les image soient nécessaires dans tous les services utilisant ce module.

Ce module est utiisé par les trois services:
- *image_crawler*:
  - pour insérer un log de fail dans la collection *db.insert_log* en cas d'échec de la requête
- *image_processor*:
  - pour insérer un log de fail ou de success dans la collection *db.insert_log* en cas d'échec: si l'image existe déjà
  - pour insérer l'image et ses metadata dans la collection *db.images*.
- *api*:
  - pour récupérer une image pour l'afficher sur le endpoint */image/<md5>*
  - pour récupérer les insert logs sur le endpoint */monitoring*

## Scale up?

J'ai essayé de scaler le nombre de workers dans les différents services, afin de voir si cela fonctionnait correctement et pouvait augmenter les performances.

En fonction du débit de nouvelles images créées dans le dossier temporaire, il est nécessaire d'avoir un nombre sufissant de services *image_processor* afin de traiter toutes les nouvelles images et ainsi ne pas laisser le nombre d'images en attente grandir.

Malheureusement je n'ai pas réussis à faire fonctionner plusieurs *image_processor* en même temps, il semblerait qu'un seul écoute réellement sur le dossier et les autres sont passifs.

En revanche j'ai bien réussis à scale up le nombre d' *image_crawler*, qui permet de crawler en parallèle les urls. J'ai réussis par exemple sur mon ordi perso à avoir 15 crawlers en parallèle et ainsi à arriver à avoir environ 500/600 images par minutes insérées dans la base.

## Et si j'avais eu plus de temps?

Si j'avais eu plus de temps, j'aurai implémenté les différents workers nécessaires. Il était si j'ai bien compris question d'avoir un event listener sur plusieurs évènements, le calcul du md5 et la transformation en niveau de gris, qui enclenchait le traitement suivant.

J'aurai également développé un petit bout de front pour pouvoir afficher l'histogramme en fonction des données de la collection. C'est également réalisable avec des librairies comme pygal qui permettent de render des données.

J'aurai passé plus de temps à l'étude de la scalabilité, pour m'assurer que la concurrence des workers ne pose pas de problèmes etc.

J'aurai également passé plus de temps sur la gestion des erreurs, afin de logger en détail les différentes erreurs.
