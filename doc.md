# Bienvenue dans Flheight 🪰

Flheight est un logiciel initialement développé pour compter et mesurer la hauteur atteinte par des mouches dans des tubes sur une image dans le cadre d'expériences en biologie. Il peut cependant être utilisé avec tout type d'image si l'on souhaite mesurer la distance entre une droite (le sol) et des points sur celle-ci.

## 1 Ouvrir une image 📁

Le bouton **Ouvrir image** permet de sélectionner une image stockée sur votre machine et de l'ouvrir dans le logiciel.

Si une image est déja ouverte et que vous avez commencé à y faire des mesures, le logiciel vous proposera **d'exporter** ces mesures au *format CSV* (voir section 4.) avant d'en ouvrir une nouvelle, et vous pouvez alors accepter, refuser ou annuler votre action.

En haut à droite de l'image, un **bouton ↻** permet de faire une rotation à 90° de l'image si nécessaire.

## 2. Définir <span style="color:red">le sol</span> 🌱 et <span style="color:green">l'échelle</span> 📏

Comme on doit mesurer la hauteur des mouches par rapport au sol, il faut commencer par dire au logiciel ou se trouve <span style="color:red">**le sol**</span> et quelle est <span style="color:green">**l'échelle**</span> de distance.

- Le bouton <span style="color:red">**Sol**</span> enclenche le <span style="color:red">**mode sol**</span>. Dans ce mode, en cliquant sur l'image, vous placez le point de départ d'un segment de droite, et en relachant le click, le point d'arrivée. Le segment du sol s'affiche alors en rouge sur l'image.

- Le bouton <span style="color:green">**Échelle**</span> enclenche le <span style="color:green">**mode échelle**</span>. Dans ce mode, en cliquant sur l'image, vous placez le point de départ d'un segment de droite, et en relachant le click, le point d'arrivée. Il faut alors indiquer la longueur de ce segment en *centimètres*. Le segment de l'échelle s'affiche en vert sur l'image.

## 3. Placer <span style="color:blue">les mouches</span> 🪰

Le bouton <span style="color:blue">**Mouche**</span> enclenche le <span style="color:blue">**mode mouche**</span>. Dans ce mode:

- **Click gauche** sur l'image place un point bleu à l'endroit du click. Celà fait également apparaître une ligne dans le tableau situé a gauche de l'image.

- **Click droit** sur un point déja tracé permet d'effacer ce point et la ligne correspondante dans le tableau.

**Remarque:** Il n'est pas possible de placer les points si l'on a pas défini <span style="color:red">**le sol**</span> et <span style="color:green">**l'échelle**</span> avant. Cela déclenchera un message d'erreur.

Le tableau renseigne diverses informations sur le point que vous venez de placer:

- **ID:** Un idendifiant unique pour chaque point;

- **Hauteur (cm):** La distance en *centimètres* entre le point et <span style="color:red">**le sol**</span> selon <span style="color:green">**l'échelle**</span> donnée;

- **Tube:** Le nom du tube dans lequel se trouve la mouche. Par défaut ce nom est "Tube 1" mais si vous souhaitez changer, il faut utiliser le **bouton Tube** pour entrer le nouveau nom **avant** de cliquer sur le point (le bouton indique quel est le nom actuel);

- **Position X (px)** et **Position Y (px):** Les coordonnées en *pixels* du point sur l'image.

A tout moment, il est possible de repasser en <span style="color:red">**mode sol**</span> ou en <span style="color:green">**mode échelle**</span> pour redéfinir l'un ou l'autre. Le logiciel **recalculera** alors toutes les hauteurs de tous les points déja placés.

## 4. Enregistrer son travail 📝

Lorsque tous vos points sont placés et que vous êtes satisfait du résultat, il ne vous reste qu'à cliquer sur le bouton **Exporter CSV** situé sous le tableau pour enregistrer ce dernier. Sélectionnez un emplacement sur votre machine et entrez un nom pour ce fichier afin de l'enregistrer au *format CSV*.