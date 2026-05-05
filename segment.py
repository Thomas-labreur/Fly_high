import cv2
import numpy as np
import matplotlib.pyplot as plt

# Charger l'image
img = cv2.imread("data/vlcsnap-2026-02-02-16h16m32s296 essai 1.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Lissage
blur = cv2.GaussianBlur(gray, (5, 5), 0)

# Seuillage (Otsu)
_, thresh = cv2.threshold(blur, 0, 255, 
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# Morphologie
kernel = np.ones((3,3), np.uint8)
opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

# Composantes connexes
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(opening)

# Filtrage par taille (pour enlever bruit)
min_area = 20
mask = np.zeros_like(opening)

for i in range(1, num_labels):  # 0 = fond
    if stats[i, cv2.CC_STAT_AREA] > min_area:
        mask[labels == i] = 255

# Résultat
plt.imshow(mask)
plt.show()