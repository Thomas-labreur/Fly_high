# Bienvenue dans Flheight 🪰

Flheight est un logiciel initialement développé pour compter et mesurer la hauteur atteinte par des mouches dans des tubes sur une image dans le cadre d'expériences en biologie. Il permet de sortir une table de mesures, ainsi qu'un ensemble feuilles excel nécessaires à faire certaines figures.

## 1 Ouvrir une image 📁

Le menu **File** vous permet d'ouvrir une image de deux façons: 

1. Le bouton **Open image** permet de sélectionner une image stockée sur votre machine et de l'ouvrir dans le logiciel.

2. Le bouton **Open video** permet de sélectionner une vidéo au format MP4 stockée sur votre machine. Une fenêtre s'ouvre alors vous permettant de choisir une frame de la vidéo à analyser.

L'image apparaît à droite de la fenêtre principale. La molette de la souris permet à tout moment de zoomer sur l'image. Le **titre du fichier** s'affiche dans le panneau de gauche. Si l'image vient d'une vidéo, le **framerate** de la vidéo ainsi que le **numéro de la frame et son timecode** s'affichent également.

**Remarque:** Si une image était déja ouverte dans le logiciel, elle est fermée et est remplacée par la nouvelle.

L'image sélectionnée peut être enregistrée au *format PNG*, via le bouton **Export image as PNG** du menu **File**. Son nom par défaut contient les informations affichées au dessus de l'image dans l'application.

Sur le panneau de Gauche, il existe une section **Image transform** permettant d'effectuer des rotations, ou bien un flip horizontal de l'image si nécessaire. Ces parmètres ne peuvent plus être modifiés à partir du moment où un <span style="color: #03caca">point</span> a été placée sur l'image (cf section 3.4).

Le menu **File** permet également d'ouvrir une table, afin d'y ajouter vos nouvelles données, ou bien de créer une nouvelle table vierge (choix par défaut à l'ouverture de l'application). Lorsqu'une table est ouverte, toutes les lignes des trials précédents sont gelées (elles ne seront plus affectées par des création / suppression de ROI mais peuvent uniquement être modifiées manuellement par double click sur une cellule).

## 2. Metadonnées

Le panneau situé à gauche de l'écran indique des métadonnées qui seront utilisées pour remplir la table.

La première section contient un ensemble d'informations qui doivent être remplies à la main. Le logiciel garde en mémoire les valeurs des champs utilisées lors de sa précédente ouverture.

Le champ "Assay mode" modifie légèrement le fonctionnement de l'application. Dans l'idée, le mode **single fly** est là pour analyser une mouche par tube et la suivre dans le temps en lui attribuant un identifiant, et le mode **group tubes** permet d'analyser plusieurs mouches par tubes sans suivi de chaque individu. En single fly, il faut donc remplir le champ **Fly ID** avec une liste d'identifiant à attribuer à chaque mouche dessinée dans ce mode, dans l'ordre.

Toute modification de ces champs modifie également les valeurs correspondantes dans la table, pour toutes les mouches de l'image en cours.

Il existe un champ "Image ID" qui donne un identifiant unique a chaque image. A chaque changement d'image, l'image ID s'incrémente. Il revient à 1 si une nouvelle table est créée.

La deuxième section indique des informations sur le fichier (image ou vidéo) qui a été chargé, et est uniquement là à titre informatif.

## 3. Les modes

Le logiciel peut être dans différents modes, ayant chacun un bouton associé à côté du menu **File**: <span style="color: #747474">Nav</span>, <span style="color:red">Ground</span>, <span style="color: #03c945">Scale</span>, <span style="color:magenta">ROI</span> et <span style="color: #03caca">Fly</span>. Chacun de ces boutons permet d'entrer dans un de ces modes, ce qui modifie la fonctionnalité de la souris.

### 3.1 <span style="color: #747474">Nav</span> ✥

Dans ce mode, le click droit de la souris permet de se déplacer sur l'image si celle-ci a été zoomée (via la molette de la souris).

### 3.2 <span style="color:red">Ground</span> 🌱 et <span style="color: #03c945">Scale</span> 📏

Comme on doit mesurer la hauteur des mouches par rapport au sol, il faut commencer par dire au logiciel ou se trouve <span style="color:red">**le sol**</span> et quelle est <span style="color: #03c945">**l'échelle**</span> de distance.

- Dans le mode <span style="color:red">**Ground**</span>, en cliquant sur l'image, vous placez le point de départ d'un segment de droite, et en relachant le click, le point d'arrivée. Le segment du sol s'affiche alors en rouge sur l'image.

- Dans le mode <span style="color: #03c945">**Scale**</span> en cliquant sur l'image, vous placez le point de départ d'un segment de droite, et en relachant le click, le point d'arrivée. Il faut alors indiquer la longueur de ce segment en *centimètres*. Le segment de l'échelle s'affiche en vert sur l'image.

### 3.3 <span style="color:magenta">ROI ⌷</span> (optionnel)

Dans le mode <span style="color:magenta">ROI</span>: 

- le **click gauche** sur l'image permet de définir des régions d'intérêt de forme rectangulaire, les ROI. La section **ROI name** du panneau de gauche permet de rentrer un nom pour chaque ROI, séparés par des virgules (à faire AVANT de tracer la ROI). Quand une ROI est créé, les mouches situées à l'intérieur avant ou apres cette création, auront leur colonne "ROI name" remplie avec ce nom. Une ROI ne peut pas être plus petite que 5x5 pixels pour éviter certains bugs.

- le **click droit** à l'intérieur d'une ROI permet de la supprimer. A ce moment là les mouches qui étaient à l'intérieur voient leur ROI name redevenir vide.

**Attention au renommage !** Si vous décidez de renommer les ROI dans le panneau de metadonnées, les noms seront réattribués **dans l'ordre où les ROI ont été dessinées**. Si les nouveaux noms sont: "ROI1, ROI2" alors la 1ère ROI dessinée recevra le nom "ROI1", la seconde "ROI2" est les autres n'auront pas de nom. 

## 3.4 <span style="color: #03caca">Fly</span> 🪰

Dans le mode <span style="color: #03caca">Fly</span>:

- **Click gauche** sur l'image place un point bleu à l'endroit du click. Celà fait également apparaître une ligne dans la table. En mode **singlefly**, il faut également donner un identifiant à la mouche. Un compteur situé en haut à droite de l'écran indique le nombre de points actuellement dessinés.

- **Click droit** sur un point déja tracé permet d'effacer ce point et la ligne correspondante dans la table. Vous pouvez aussi effacer toutes les mouches de l'image en cours à l'aide du bouton **Delete all flies**. 

**Remarque:** Il n'est pas possible de placer les points si l'on a pas défini <span style="color:red">**le sol**</span> et <span style="color: #03c945">**l'échelle**</span> avant. Cela déclenchera un message d'erreur.

Le tableau renseigne diverses informations sur le point que vous venez de placer:

- **Point ID:** Un idendifiant unique pour chaque point;

- **Fly ID:** Pour les **single flies**, permet d'identifier une même mouche présentes sur plusieurs images.

- **Height (cm):** La distance en *centimètres* entre le point et <span style="color:red">**le sol**</span> selon <span style="color: #03c945">**l'échelle**</span> donnée. Cette hauteur est la distance **orthogonale** du point à la droite du <span style="color:red">sol</span>;

- **X position (px)** et **Y position (px):** Les coordonnées en *pixels* du point sur l'image.

- Ainsi que toutes les métadonnées visible dans le panneau de gauche (ou définies à la création des ROI).

## 4. Auto-détection des mouches

Le bouton **Automatic Detection** permet de détecter automatiquement toutes les mouches situées dans les ROI actuellement définies. Elles apparaissent alors comme des <span style="color:blue">**cercles bleus**</span> plus foncés que les mouches placées <span style="color: #03caca">manuellement</span>, et la colonne "source" de la table indique si la mouche a été annotée automatiquement ou manuellement. Les mouches détectées ainsi ne peuvent être qu'en mode **group tubes**

Ces mouches peuvent êtres effacées en mode <span style="color: #03caca">**Fly**</span> comme les autres, avec le **click droit**.

La détection automatique fonctionne par seuillage et suppose que les mouches sont des points **sombres** sur un fond **clair**. Dans le panneau de gauche, la section **Auto-detection** permet d'ajuster le seuil d'intensité lumineuse qui délimite les mouches du fond, ainsi que la taille min et max des mouches (aide quand les mouches sont collées les unes aux autres)

## 5. Mises à jour de la table

A tout moment, il est possible de repasser en <span style="color:red">**mode sol**</span>, en <span style="color:green">**mode échelle**</span> pour redéfinir l'un ou l'autre. Le logiciel **recalculera** alors toutes les hauteurs de tous les points déja placés.

On peut également repasser en <span style="color:magenta">**mode ROI**</span> pour ajouter ou supprimer des ROI. Si des mouches étaient présentes dans une ROI supprimé, leur ROI name redevient vide. De même, si une ROI est ajoutée et que des mouches se trouvent déja à l'intérieur, les lignes correspondantent se mettent à jour avec le nom de la nouvelle ROI.

## 6. Navigation dans la vidéo.

Parfois un fichier vidéo contient plusieurs éssais. On peut donc ré-ouvrir la vidéo à l'aide du bouton **Navigate video** du menu **File**. Si on le fait, les mouches précédentes disparaissent de l'image mais restent dans la table et deviennent **figées**. Elles ne peuvent plus être recalculées, la seule façon de les modifier est manuellement, en cliquant sur la case de la table.

Rien n'empêche alors de créer de nouveaux ROI, redéfinir l'échelle, le sol ou changer les métadonnées sans que celà n'impacte les données des trials précédents.

## 7. Enregistrer son travail 📝

Lorsque tous vos points sont placés et que vous êtes satisfait du résultat, vous pouvez cliquer sur le bouton **Export table as CSV** situé dans le menu **File** pour enregistrer ce dernier. Sélectionnez un emplacement sur votre machine et entrez un nom pour ce fichier afin de l'enregistrer au *format CSV*.

Le bouton ***Export figure-ready as XLSX** permet de générer un fichier excel contenant différentes feuilles construites à partir de la table, pensées pour générer des figures facilement via excel. La liste de ces feuilles est la suivantes:

- **raw_data**: la table telle que dans le logiciel;

- **FIG_all_boxplot:** une colonne par age contenant toutes lesmesures de hauteurs des mouches de cet age, sans ordre particulier, pour faire des boxplots;

- **FIG_all_dispersion:** une ligne par age avec des mesures statistiques de la dispersion des hauteurs, dont la upper_dispersion (voire ci-dessous).

- **FIG_single_boxplot:** comme le figure_points_wide mais uniquement pour les single_flies;

- **FIG_single_dispersion:** comme figure_dispersion mais uniquement pour les single_flies.

**Note:** L'**upper dispersion** est l'écart moyen des hauteurs supérieures à la moyenne à celle-ci. C'est donc un écart-type qui ne prend en compte que les valeurs supérieures à la moyenne. Elle est utile quand la distribution est asymétrique, par exemple ici, les hauteurs ne peuvent pas être négatives mais peuvent s'étaler au dessus de la moyenne comme elles le veulent. La différence entre la variabilité de deux groupes (jeunes et vieux par ex) se verra donc nettement mieux dans les grandes hauteurs que dans les petites. Le **relative upper dispersion** est le ratio de l'upper dispersion par la moyenne.