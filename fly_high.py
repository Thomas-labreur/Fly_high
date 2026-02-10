import sys, csv
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem, QGraphicsEllipseItem, QFileDialog,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QInputDialog, QToolButton, QMessageBox
)
from PyQt6.QtGui import QPixmap, QPen, QIcon
from PyQt6.QtCore import Qt, QPointF, QLineF

class ImageView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.mode = None
        self.temp_line = None
        self.start_point = None
        self.parent = None
        self.last_line = None
        self.zoom_factor = 1.15

        # Transformation centrée sur la souris
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

    def wheelEvent(self, event):
        """Zoom in/out centré sur la souris (PyQt6 / PySide6)"""
        # Position de la souris dans la scène avant le zoom
        mouse_scene_pos = self.mapToScene(event.position().toPoint())

        # Zoom in/out
        zoom = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
        self.scale(zoom, zoom)

        # Ajuster le scroll pour garder le point sous la souris fixe
        new_mouse_scene_pos = self.mapToScene(event.position().toPoint())
        delta = new_mouse_scene_pos - mouse_scene_pos
        self.translate(delta.x(), delta.y())


    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        if self.mode in ["sol", "scale"]:
            self.start_point = pos
            # supprimer l'ancienne ligne si elle existe
            if self.last_line:
                self.scene().removeItem(self.last_line)
                self.last_line = None

            self.temp_line = QGraphicsLineItem()
            color = Qt.GlobalColor.red if self.mode == "sol" else Qt.GlobalColor.green
            self.temp_line.setPen(QPen(color, 2))
            self.scene().addItem(self.temp_line)

        elif self.mode == "fly":

            if event.button() == Qt.MouseButton.RightButton:  # clic droit pour supprimer

                # On récupère tous les items à cet endroit
                items = self.scene().items(pos)
                
                for item in items:
                    # Vérifie si c'est un point de mouche (Ellipse bleu)
                    if isinstance(item, QGraphicsEllipseItem):
                        self.parent.remove_fly(item)
                        break

            else:
                self.parent.add_fly(pos)

    def mouseMoveEvent(self, event):
        if self.temp_line:
            pos = self.mapToScene(event.pos())
            self.temp_line.setLine(
                self.start_point.x(), self.start_point.y(),
                pos.x(), pos.y()
            )

    def mouseReleaseEvent(self, event):
        if self.temp_line:
            line = self.temp_line.line()
            if self.mode == "sol":
                self.parent.set_ground(line)
            elif self.mode == "scale":
                self.parent.set_scale(line)

            # garder cette ligne pour suppression ultérieure
            self.last_line = self.temp_line
            self.temp_line = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mesure hauteur des mouches")

        self.scene = QGraphicsScene()
        self.view = ImageView(self.scene)
        self.view.parent = self

        # Ligne et échelle
        self.ground_line_item = None
        self.scale_line_item = None
        self.ground_line = None
        self.scale_line = None
        self.scale_cm_per_px = None
        self.current_tube = "Tube 1"

        # Points des mouches
        self.fly_points = []

        # Table pour afficher les mesures
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Hauteur (cm)", "Tube", "Position X (px)", "Position Y (px)"])

        # Boutons pour les modes
        self.buttons = {}
        buttons_layout = QHBoxLayout()
        modes = [("Sol", "sol", "red"), ("Échelle", "scale", "lightgreen"), ("Mouche", "fly", "#4169E1")]
        for name, mode, color in modes:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, m=mode: self.set_mode(m))
            btn.setStyleSheet("background-color: lightgray")
            buttons_layout.addWidget(btn)
            self.buttons[mode] = {"button": btn, "color": color}

        # Bouton tube
        self.tube_btn = QPushButton(f"Tube: {self.current_tube}")
        self.tube_btn.clicked.connect(self.set_tube)
        self.tube_btn.setStyleSheet("background-color: lightgray")
        buttons_layout.addWidget(self.tube_btn)

        # Layout table + bouton d'export
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        export_btn = QPushButton("Exporter CSV")
        export_btn.clicked.connect(self.export_csv)
        table_layout.addWidget(export_btn)

        # Layout table + image
        content_layout = QHBoxLayout()
        content_layout.addLayout(table_layout)
        content_layout.addWidget(self.view, 1) # stretch = 1 pour prendre le reste de l'espace

        # Bouton de rotation de l'image de 90°
        self.rotate_btn = QToolButton(self.view)
        self.rotate_btn.setText("↻")  
        self.rotate_btn.setStyleSheet("""
            background-color: rgba(255,255,255,200);
            border: 1px solid gray;
            border-radius: 10px;
        """)
        self.rotate_btn.resize(30, 30)
        self.rotate_btn.clicked.connect(self.rotate_image)
        self.update_rotate_btn_position()

        # Layout principal
        layout = QVBoxLayout()
        layout.addLayout(buttons_layout)
        layout.addLayout(content_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_image()

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir image")
        if path:
            pixmap = QPixmap(path)
            self.pixmap_item = self.scene.addPixmap(pixmap)
            self.pixmap_item.setTransformOriginPoint(self.pixmap_item.boundingRect().center())

    def set_mode(self, mode):
        self.view.mode = mode

        # Mettre tous les boutons en gris clair
        for m, info in self.buttons.items():
            info["button"].setStyleSheet("background-color: lightgray")

        # Colorer le bouton actif selon sa couleur
        if mode in self.buttons:
            self.buttons[mode]["button"].setStyleSheet(f"background-color: {self.buttons[mode]['color']}")

    def set_tube(self):
        tube, ok = QInputDialog.getText(self, "Nom du tube", "Entrer le nom du tube:")
        if ok and tube:
            self.current_tube = tube
            self.tube_btn.setText(f"Tube: {self.current_tube}")

    def set_ground(self, line):
        # Supprime l'ancienne ligne du sol si elle existe
        if self.ground_line_item is not None:
            self.scene.removeItem(self.ground_line_item)
            self.ground_line_item = None

        # Crée et ajoute la nouvelle ligne du sol
        self.ground_line_item = QGraphicsLineItem(line)
        self.ground_line_item.setPen(QPen(Qt.GlobalColor.red, 2))
        self.scene.addItem(self.ground_line_item)

        # Stocke la géométrie pour les calculs
        self.ground_line = line

        # Recalculer les hauteurs pour toutes les mouches
        self.recalculate_heights()

    def set_scale(self, line):
        # Supprime l'ancienne ligne de l'échelle si elle existe
        if self.scale_line_item is not None:
            self.scene.removeItem(self.scale_line_item)
            self.scale_line_item = None

        # Demande la longueur réelle en cm
        cm, ok = QInputDialog.getDouble(
            self, "Échelle", "Longueur réelle (cm):"
        )
        if not ok:
            return

        # Crée et ajoute la nouvelle ligne d'échelle
        self.scale_line_item = QGraphicsLineItem(line)
        self.scale_line_item.setPen(QPen(Qt.GlobalColor.green, 2))
        self.scene.addItem(self.scale_line_item)

        # Stocke la géométrie et le ratio cm/px
        self.scale_line = line
        length_px = np.hypot(line.dx(), line.dy())
        self.scale_cm_per_px = cm / length_px

        # Recalculer les hauteurs pour toutes les mouches
        self.recalculate_heights()

    def add_fly(self, pos):
        
        # Affichage d'un message d'erreur
        if not self.ground_line or not self.scale_cm_per_px:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Erreur")
                msg.setText("Définir d'abord le sol et l'échelle avant d'ajouter une mouche !")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return

        # Point
        r = 4
        point = QGraphicsEllipseItem(pos.x()-r, pos.y()-r, 2*r, 2*r)
        point.setPen(QPen(Qt.GlobalColor.blue))
        self.scene.addItem(point)

        # Mise à jour de la table
        self.fly_points.append({"item": point, "pos": pos, "tube": self.current_tube})
        self.recalculate_heights()

    def remove_fly(self, item):
        # Retirer le point de la scène
        self.scene.removeItem(item)

        # Retirer de la liste fly_points
        self.fly_points = [f for f in self.fly_points if f["item"] != item]

        # Recalculer les hauteurs dans le tableau
        self.recalculate_heights()


    def recalculate_heights(self):
        """Recalculer toutes les hauteurs dans la table selon le sol et l'échelle actuels."""
        self.table.setRowCount(0)
        if not self.ground_line or not self.scale_cm_per_px:
            return

        for idx, fly in enumerate(self.fly_points):
            pos = fly["pos"]
            height_px = self.point_to_line_distance(pos, self.ground_line)
            height_cm = height_px * self.scale_cm_per_px

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.table.setItem(row, 1, QTableWidgetItem(f"{height_cm:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(fly["tube"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{pos.x():.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{pos.y():.2f}"))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_rotate_btn_position()

    def update_rotate_btn_position(self):
        margin = 10
        # Détecte la largeur de la scrollbar verticale
        scrollbar_width = self.view.verticalScrollBar().width()
        x = self.view.width() - self.rotate_btn.width() - margin - scrollbar_width
        y = margin
        self.rotate_btn.move(x, y)

    def rotate_image(self):
        if hasattr(self, "pixmap_item"):
            self.pixmap_item.setRotation(self.pixmap_item.rotation() + 90)




    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer CSV", "", "Fichiers CSV (*.csv)"
        )
        if not path:
            return

        # Exporter la table
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # écrire l'en-tête
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            # écrire les lignes
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)

            

    @staticmethod
    def point_to_line_distance(P, line):
        A = np.array([line.x1(), line.y1()])
        B = np.array([line.x2(), line.y2()])
        P = np.array([P.x(), P.y()])
        return np.abs(np.cross(B - A, A - P)) / np.linalg.norm(B - A)



app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
