# Bienvenue dans Flheight 🪰

Flheight est un logiciel initialement développé pour compter et mesurer la hauteur atteinte par des mouches dans des tubes sur une image dans le cadre d'expériences en biologie. Il permet de sortir une table de mesures, ainsi qu'un ensemble feuilles excel nécessaires à faire certaines figures.

## 1 Ouvrir une image 📁

Le menu **File** vous permet d'ouvrir une image de deux façons: 

1. Le bouton **Open image** permet de sélectionner une image stockée sur votre machine et de l'ouvrir dans le logiciel.

2. Le bouton **Open video** permet de sélectionner une vidéo au format MP4 stockée sur votre machine. Une fenêtre s'ouvre alors vous permettant de choisir une frame de la vidéo à analyser.

L'image apparaît à droite de la fenêtre principale et le titre du fichier s'affiche au dessus. Si l'image vient d'une vidéo, le **framerate** de la vidéo ainsi que le **numéro de la frame et son timecode** s'affichent également.

Sur le panneau de Gauche, il existe une section **Image transform** permettant d'effectuer des rotations de 90°, ou bien un flip horizontal de l'image si nécessaire.

Le menu **File** permet également d'ouvrir une table, afin d'y ajouter vos nouvelles données, ou bien de créer une nouvelle table vierge (choix par défaut à l'ouverture de l'application). Lorsqu'une table est ouverte, toutes les lignes des trials précédents sont gelées (elles ne seront plus affectées par des création / suppression de ROI mais peuvent uniquement être modifiées manuellement par double click sur une cellule).

## 2. Metadonnées

Le panneau situé à gauche de l'écran indique des métadonnées.

La première section contient un ensemble d'informations qui doivent être remplies à la main. Le logiciel garde en mémoire les valeurs des champs utilisées lors de sa précédente ouverture.

Le champ "Assay mode" modifie légèrement le fonctionnement de l'application. Dans l'idée, le mode **single fly** est là pour analyser une mouche par tube et la suivre dans le temps en lui attribuant un identifiant, et le mode **group tubes** permet d'analyser plusieurs mouches par tubes sans suivi de chaque individu. En single fly, il faut donc remplir le champ **Fly ID** avec une liste d'identifiant à attribuer à chaque mouche dessinée dans ce mode, dans l'ordre.

Il existe un champ "Trial". Un trial correspond à 1 image. A chaque changement d'image, le trial s'incrémente. Il revient à 1 si une nouvelle table est créée.

La deuxième section indique des informations sur le fichier (image ou vidéo) qui a été chargé, et est uniquement là à titre informatif.

## 3. Définir <span style="color:red">le sol</span> 🌱 et <span style="color:green">l'échelle</span> 📏

Comme on doit mesurer la hauteur des mouches par rapport au sol, il faut commencer par dire au logiciel ou se trouve <span style="color:red">**le sol**</span> et quelle est <span style="color:green">**l'échelle**</span> de distance.

- Le bouton <span style="color:red">**Ground**</span> enclenche le <span style="color:red">**mode sol**</span>. Dans ce mode, en cliquant sur l'image, vous placez le point de départ d'un segment de droite, et en relachant le click, le point d'arrivée. Le segment du sol s'affiche alors en rouge sur l'image.

- Le bouton <span style="color:green">**Scale**</span> enclenche le <span style="color:green">**mode échelle**</span>. Dans ce mode, en cliquant sur l'image, vous placez le point de départ d'un segment de droite, et en relachant le click, le point d'arrivée. Il faut alors indiquer la longueur de ce segment en *centimètres*. Le segment de l'échelle s'affiche en vert sur l'image.

## 4. Définir des <span style="color:magenta">ROI</span> (optionnel)

Le bouton <span style="color:magenta">**ROI**</span> enclenche le <span style="color:magenta">**mode ROI**</span>. Dans ce mode: 

- le **click gauche** sur l'image permet de définir des régions d'intérêt de forme rectangulaire, les ROI. La section **ROI name** du panneau de gauche permet de rentrer un nom pour chaque ROI, séparés par des virgules (à faire AVANT de tracer la ROI). Quand une ROI est créé, les mouches situées à l'intérieur avant ou apres cette création, auront leur colonne "ROI name" remplie avec ce nom.

- le **click droit** à l'intérieur d'une ROI permet de la supprimer. A ce moment là les mouches qui étaient à l'intérieur voient leur ROI name redevenir vide.

## 5. Placer <span style="color:cyan">les mouches</span> 🪰

Le bouton <span style="color:cyan">**Fly**</span> enclenche le <span style="color:cyan">**mode mouche**</span>. Dans ce mode:

- **Click gauche** sur l'image place un point bleu à l'endroit du click. Celà fait également apparaître une ligne dans la table. En mode **singlefly**, il faut également donner un identifiant à la mouche

- **Click droit** sur un point déja tracé permet d'effacer ce point et la ligne correspondante dans la table.

**Remarque:** Il n'est pas possible de placer les points si l'on a pas défini <span style="color:red">**le sol**</span> et <span style="color:green">**l'échelle**</span> avant. Cela déclenchera un message d'erreur.

Le tableau renseigne diverses informations sur le point que vous venez de placer:

- **Point ID:** Un idendifiant unique pour chaque point;

- **Fly ID:** Pour les **single flies**, permet d'identifier une même mouche présentes sur plusieurs images.

- **Height (cm):** La distance en *centimètres* entre le point et <span style="color:red">**le sol**</span> selon <span style="color:green">**l'échelle**</span> donnée;

- **X position (px)** et **Y position (px):** Les coordonnées en *pixels* du point sur l'image.

- Ainsi que toutes les métadonnées visible dans le panneau de gauche (ou définies à la création des ROI).

## 5. Auto-détection des mouches

Le bouton **Automatic Detection** permet de détecter automatiquement toutes les mouches situées dans les ROI actuellement définies. Elles apparaissent alors comme des <span style="color:blue">**cercles bleus**</span> plus foncés que les mouches placées manuellement, et la colonne "source" de la table indique si la mouche a été annotée automatiquement ou manuellement. Les mouches détectées ainsi ne peuvent être qu'en mode **group tubes**

Ces mouches peuvent êtres effacées en <span style="color:cyan">**mode mouche**</span> comme les autres, avec le **click droit**.

La détection automatique fonctionne par seuillage et suppose que les mouches sont des points **sombres** sur un fond **clair**. Dans le panneau de gauche, la section **Auto-detection** permet d'ajuster le seuil d'intensité lumineuse qui délimite les mouches du fond, ainsi que la taille min et max des mouches (aide quand les mouches sont collées les unes aux autres)

## 6. Mises à jour de la table

A tout moment, il est possible de repasser en <span style="color:red">**mode sol**</span>, en <span style="color:green">**mode échelle**</span> pour redéfinir l'un ou l'autre. Le logiciel **recalculera** alors toutes les hauteurs de tous les points déja placés.

On peut également repasser en <span style="color:magenta">**mode ROI**</span> pour ajouter ou supprimer des ROI. Si des mouches étaient présentes dans une ROI supprimée, alors les lignes correspondantes prennent les métadonnées par défaut (définies dans le panneau de gauche). De même, si une ROI est ajoutée et que des mouches se trouvent déja à l'intérieur, les lignes correspondantent se mettent à jour avec les métadonnées de la nouvelle ROI.

## 7. Navigation dans la vidéo.

Parfois un fichier vidéo contient plusieurs éssais (trials). On peut donc ré-ouvrir la vidéo à l'aide du bouton **Select Next Trial** du menu **File**. Si on le fait, les mouches précédentes disparaissent de l'image mais restent dans la table et deviennent **figées**. Elles ne peuvent plus être recalculées, la seule façon de les modifier est manuellement, en cliquant sur la case de la table.

Rien n'empêche alors de créer de nouveaux ROI, redéfinir l'échelle, le sol ou changer les métadonnées sans que celà n'impacte les données des trials précédents.

## 4. Enregistrer son travail 📝

L'image analysée peut être enregistrée au *format PNG*, via le bouton **Export image as PNG** du menu **File**. Son nom par défaut contient les informations affichées au dessus de l'image dans l'application.

Lorsque tous vos points sont placés et que vous êtes satisfait du résultat, vous ppuvez cliquer sur le bouton **Export table as CSV** situé dans le menu **File** pour enregistrer ce dernier. Sélectionnez un emplacement sur votre machine et entrez un nom pour ce fichier afin de l'enregistrer au *format CSV*.

Le bouton ***Export figure-ready as XLSX** permet de générer un fichier excel contenant différentes feuilles construites à partir de la table, pensées pour générer des figures facilement via excel. La liste de ces feuilles est la suivantes:

- **raw_data**: la table telle que dans le logiciel;

- **FIG_all_boxplot:** une colonne par age contenant toutes lesmesures de hauteurs des mouches de cet age, sans ordre particulier, pour faire des boxplots;

- **FIG_all_dispersion:** une ligne par age avec des mesures statistiques de la dispersion des hauteurs, dont la upper_dispersion (voire ci-dessous).

- **FIG_single_boxplot:** comme le figure_points_wide mais uniquement pour les single_flies;

- **FIG_single_dispersion:** comme figure_dispersion mais uniquement pour les single_flies.

**Note:** L'**upper dispersion** est l'écart moyen des hauteurs supérieures à la moyenne à celle-ci. C'est donc un écart-type qui ne prend en compte que les valeurs supérieures à la moyenne. Elle est utile quand la distribution est asymétrique, par exemple ici, les hauteurs ne peuvent pas être négatives mais peuvent s'étaler au dessus de la moyenne comme elles le veulent. La différence entre la variabilité de deux groupes (jeunes et vieux par ex) se verra donc nettement mieux dans les grandes hauteurs que dans les petites. Le **relative upper dispersion** est le ratio de l'upper dispersion par la moyenne.