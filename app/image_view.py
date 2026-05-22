from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsLineItem, 
    QGraphicsEllipseItem, QGraphicsRectItem
)
from PyQt6.QtGui import QPen
from PyQt6.QtCore import Qt


class ImageView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.mode = None
        self.temp_line = None
        self.temp_rect = None
        self.start_point = None
        self.parent = None
        self.last_line = None
        self.zoom_factor = 1.15
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

    def wheelEvent(self, event):
        mouse_scene_pos = self.mapToScene(event.position().toPoint())
        zoom = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
        self.scale(zoom, zoom)
        new_mouse_scene_pos = self.mapToScene(event.position().toPoint())
        delta = new_mouse_scene_pos - mouse_scene_pos
        self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        if self.mode in ["ground", "scale"]:
            self.start_point = pos
            if self.last_line:
                self.scene().removeItem(self.last_line)
                self.last_line = None
            self.temp_line = QGraphicsLineItem()
            color = Qt.GlobalColor.red if self.mode == "ground" else Qt.GlobalColor.green
            self.temp_line.setPen(QPen(color, 4))
            self.scene().addItem(self.temp_line)
        elif self.mode == "roi":
            if event.button() == Qt.MouseButton.RightButton:
                items = self.scene().items()  # tous les items
                for item in items:
                    if isinstance(item, QGraphicsRectItem) and item.rect().contains(pos):
                        self.parent.remove_roi(item)
                        break
            else:
                self.start_point = pos
                self.temp_rect = QGraphicsRectItem()
                self.temp_rect.setPen(QPen(Qt.GlobalColor.magenta, 4))
                self.scene().addItem(self.temp_rect)
        elif self.mode == "fly":
            if event.button() == Qt.MouseButton.RightButton:
                items = self.scene().items(pos)
                for item in items:
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

        elif self.temp_rect:
            pos = self.mapToScene(event.pos())
            x,y = self.start_point.x(), self.start_point.y()
            w = pos.x() - x
            h = pos.y() - y
            self.temp_rect.setRect(x, y, w, h)


    def mouseReleaseEvent(self, event):
        if self.temp_line:
            line = self.temp_line.line()
            if self.mode == "ground":
                self.parent.set_ground(line)
            elif self.mode == "scale":
                self.parent.set_scale(line)
            self.last_line = self.temp_line
            self.scene().removeItem(self.temp_line)
            self.temp_line = None
            
        if self.temp_rect:
            rect = self.temp_rect.rect()
            self.scene().removeItem(self.temp_rect)  
            self.temp_rect = None
            self.parent.add_roi(rect)
            