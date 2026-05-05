import sys, csv, os, markdown
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem, QGraphicsEllipseItem, QFileDialog,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QInputDialog, QToolButton, QMessageBox,
    QDialog, QTextBrowser, QSplitter, QSlider, QLabel, QSpinBox,
    QDialogButtonBox, QMenu, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QPen, QImage
from PyQt6.QtCore import Qt, QSettings

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

def resource_path(relative_path):
    """Get absolute path (for pyinstaller)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class VideoFrameSelector(QDialog):
    """Dialog to select a frame in a video."""

    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Frame selection")
        self.resize(900, 620)
        self.video_path = video_path
        self.selected_pixmap = None

        # Open video
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25

        # --- Main layout ---
        layout = QVBoxLayout(self)

        # Frame preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(400)
        self.preview_label.setStyleSheet("background-color: #111; border-radius: 6px;")
        layout.addWidget(self.preview_label)

        # Frame informations
        info_layout = QHBoxLayout()
        self.frame_info_label = QLabel("Frame : 0")
        self.frame_info_label.setStyleSheet("color: #555; font-size: 11px;")
        self.time_info_label = QLabel("Temps : 0.00 s")
        self.time_info_label.setStyleSheet("color: #555; font-size: 11px;")
        info_layout.addWidget(self.frame_info_label)
        info_layout.addWidget(self.time_info_label)
        info_layout.addStretch()
        self.fps_label = QLabel(f"FPS : {self.fps:.2f}")
        self.fps_label.setStyleSheet("color: #555; font-size: 11px;")
        info_layout.addWidget(self.fps_label)
        layout.addLayout(info_layout)

        # Navigation slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, self.total_frames - 1))
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider)

        # Navigation buttons (fine + spinbox)
        nav_layout = QHBoxLayout()

        btn_prev10 = QPushButton("« -10")
        btn_prev10.clicked.connect(lambda: self.step_frames(-10))
        btn_prev = QPushButton("‹ -1")
        btn_prev.clicked.connect(lambda: self.step_frames(-1))

        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(0)
        self.spinbox.setMaximum(max(0, self.total_frames - 1))
        self.spinbox.setValue(0)
        self.spinbox.setPrefix("Frame : ")
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)

        btn_next = QPushButton("+1 ›")
        btn_next.clicked.connect(lambda: self.step_frames(1))
        btn_next10 = QPushButton("+10 »")
        btn_next10.clicked.connect(lambda: self.step_frames(10))
        btn_goto = QPushButton("Go to…")
        btn_goto.clicked.connect(self.goto_frame_dialog)
        

        for btn in [btn_prev10, btn_prev]:
            btn.setFixedWidth(70)
        for btn in [btn_next, btn_next10]:
            btn.setFixedWidth(70)

        nav_layout.addWidget(btn_prev10)
        nav_layout.addWidget(btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.spinbox)
        nav_layout.addStretch()
        nav_layout.addWidget(btn_next)
        nav_layout.addWidget(btn_next10)
        nav_layout.addWidget(btn_goto)
        layout.addLayout(nav_layout)

        # Ok / cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Display first frame
        self._current_frame_index = 0
        self._updating = False
        self.show_frame(0)

    def show_frame(self, index):
        """Displays the frame from its index."""
        index = max(0, min(index, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.cap.read()
        if not ret:
            return

        # Convert BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # Scaling for preview
        preview_size = self.preview_label.size()
        scaled = pixmap.scaled(preview_size, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

        # Store full resolution pixmap to export
        self.selected_pixmap = pixmap
        self._current_frame_index = index

        # Update informations
        self.frame_info_label.setText(f"Frame : {index} / {self.total_frames - 1}")
        time_s = index / self.fps if self.fps else 0
        self.time_info_label.setText(f"Time : {time_s:.2f} s")

    def on_slider_changed(self, value):
        if self._updating:
            return
        self._updating = True
        self.spinbox.setValue(value)
        self.show_frame(value)
        self._updating = False

    def on_spinbox_changed(self, value):
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(value)
        self.show_frame(value)
        self._updating = False

    def goto_frame_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Go to…")
        layout = QVBoxLayout(dialog)

        # Frame or Time choice
        mode_layout = QHBoxLayout()
        btn_frame = QPushButton("By frame")
        btn_time = QPushButton("By time (s)")
        mode_layout.addWidget(btn_frame)
        mode_layout.addWidget(btn_time)
        layout.addLayout(mode_layout)

        def go_by_frame():
            index, ok = QInputDialog.getInt(self, "Go to…", "Frame index :",
                                            self._current_frame_index, 0, self.total_frames - 1)
            if ok:
                self.step_frames(index - self._current_frame_index)
            dialog.accept()

        def go_by_time():
            max_s = (self.total_frames - 1) / self.fps if self.fps else 0
            current_s = self._current_frame_index / self.fps if self.fps else 0
            seconds, ok = QInputDialog.getDouble(self, "Go to…", "Time (sec) :",
                                                current_s, 0, max_s, 2)
            if ok:
                index = int(round(seconds * self.fps))
                self.step_frames(index - self._current_frame_index)
            dialog.accept()

        btn_frame.clicked.connect(go_by_frame)
        btn_time.clicked.connect(go_by_time)

        dialog.exec()

    def step_frames(self, delta):
        new_index = self._current_frame_index + delta
        new_index = max(0, min(new_index, self.total_frames - 1))
        self._updating = True
        self.slider.setValue(new_index)
        self.spinbox.setValue(new_index)
        self.show_frame(new_index)
        self._updating = False

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Refresh preview when zooming
        self.show_frame(self._current_frame_index)


class ImageView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.mode = None
        self.temp_line = None
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
            self.temp_line.setPen(QPen(color, 2))
            self.scene().addItem(self.temp_line)

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

    def mouseReleaseEvent(self, event):
        if self.temp_line:
            line = self.temp_line.line()
            if self.mode == "ground":
                self.parent.set_ground(line)
            elif self.mode == "scale":
                self.parent.set_scale(line)
            self.last_line = self.temp_line
            self.temp_line = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flheight")

        self.settings = QSettings("Config", "Flheight")
        self.column_names = self.settings.value(
            "table/column_names", 
            defaultValue=["ID", "Height (cm)", "Tube", "X position (px)", "Y position (px)"]
        )

        self.scene = QGraphicsScene()
        self.view = ImageView(self.scene)
        self.view.parent = self

        self.ground_line_item = None
        self.scale_line_item = None
        self.ground_line = None
        self.scale_line = None
        self.scale_cm_per_px = None
        self.current_group = "Tube 1"

        self.fly_points = []

        self.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
            }
            QPushButton:hover {
                background-color: #b0b0b0;
            }
            QHeaderView::section:hover {
                background-color: lightgray;
            }
        """)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(self.column_names)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.rename_column)
        self.table.horizontalHeader().setToolTip("Double click to rename column.")

        # --- Buttons ---
        buttons_layout = QHBoxLayout()

        file_btn = QPushButton("File")
        file_menu = QMenu(self)
        file_menu.addAction("Open image", self.open_image)
        action_video = file_menu.addAction("Open video", self.open_video)
        if not CV2_AVAILABLE:
            action_video.setEnabled(False)
        self.export_frame_action = file_menu.addAction("Export image as PNG", self.export_frame)
        self.export_frame_action.setEnabled(False)
        file_menu.addSeparator()
        file_menu.addAction("Export table as CSV", self.export_csv)
        file_btn.setMenu(file_menu)
        buttons_layout.addWidget(file_btn)

        # Modes buttons
        self.buttons = {}
        modes = [("Ground", "ground", "red"), ("Scale", "scale", "lightgreen"), ("Fly", "fly", "#4169E1")]
        for name, mode, color in modes:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, m=mode: self.set_mode(m))
            btn.setEnabled(False)
            buttons_layout.addWidget(btn)
            self.buttons[mode] = {"button": btn, "color": color}

        # Group button
        self.group_btn = QPushButton(f"{self.column_names[2]}: {self.current_group}")
        self.group_btn.clicked.connect(self.set_group)
        buttons_layout.addWidget(self.group_btn)

        # Help button
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        buttons_layout.addWidget(help_btn)

        # --- Table + export ---
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)

        # Layout for table and image view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        splitter.addWidget(table_widget)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        content_layout = QHBoxLayout()
        content_layout.addWidget(splitter)

        # Label for image informations
        self.image_info_label = QLabel("")
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_info_label.setStyleSheet("color: #555; font-size: 11px;")
        self.image_info_label.setFixedHeight(20)
        self.image_info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Rotation button
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

        # Global layout
        layout = QVBoxLayout()
        layout.addLayout(buttons_layout)
        layout.addWidget(self.image_info_label)
        layout.addLayout(content_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------ #
    #  Open image
    # ------------------------------------------------------------------ #
    def open_image(self):
        if self.table.rowCount() > 0:
            reply = QMessageBox.question(
                self,
                "Exporter before open",
                "Do you want to export your work before opening a new image ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.export_csv()

        self.clear_scene()

        path, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._load_pixmap(QPixmap(path))
            filename = os.path.basename(path)
            self.image_info_label.setText(filename)
            self.default_export_name = os.path.splitext(filename)[0]

    # ------------------------------------------------------------------ #
    #  Open video
    # ------------------------------------------------------------------ #
    def open_video(self):
        if not CV2_AVAILABLE:
            QMessageBox.warning(self, "Missing module",
                                "opencv-python module is required.\n"
                                "Install with : pip install opencv-python")
            return

        if self.table.rowCount() > 0:
            reply = QMessageBox.question(
                self,
                "Export before open",
                "Do you want to export your work before opening a new image ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.export_csv()

        path, _ = QFileDialog.getOpenFileName(
            self, "Open video", "", "Videos (*.mp4 *.avi *.mov *.mkv)"
        )
        if not path:
            return

        # Open frame selctor
        dialog = VideoFrameSelector(path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_pixmap:
            self.clear_scene()
            self._load_pixmap(dialog.selected_pixmap, from_video=True)
            videoname = os.path.basename(path)
            frame = dialog._current_frame_index
            timecode = frame / dialog.fps
            info = f"{videoname} | Framerate: {dialog.fps:.2f} FPS | Frame: {frame} ({timecode:.2f}s)"
            self.image_info_label.setText(info)
            self.default_export_name = f"{os.path.splitext(videoname)[0]}_frame{frame}_{timecode:.2f}s"

    # ------------------------------------------------------------------ #
    #  Loading QPixmap in the scene
    # ------------------------------------------------------------------ #
    def _load_pixmap(self, pixmap: QPixmap, from_video=False):
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.image_width = pixmap.width()
        self.image_height = pixmap.height()
        self.pixmap_item.setTransformOriginPoint(self.pixmap_item.boundingRect().center())
        self.scene_group = self.scene.createItemGroup([self.pixmap_item])
        self.scene_group.setTransformOriginPoint(self.pixmap_item.boundingRect().center())
        self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.current_pixmap = pixmap
        self.export_frame_action.setEnabled(from_video)
        for mode, info in self.buttons.items():
            info["button"].setEnabled(True)

    # ------------------------------------------------------------------ #
    #  Clear the scene
    # ------------------------------------------------------------------ #
    def clear_scene(self):
        self.scene.clear()
        self.image_info_label.setText("")
        self.default_export_name = ""
        self.ground_line_item = None
        self.scale_line_item = None
        self.ground_line = None
        self.scale_line = None
        self.scale_cm_per_px = None
        self.view.last_line = None
        self.view.temp_line = None
        self.view.start_point = None
        self.fly_points = []
        self.table.setRowCount(0)
        self.current_group = "Tube 1"
        self.group_btn.setText(f"Group : {self.current_group}")
        for mode, info in self.buttons.items():
            info["button"].setEnabled(False)

    # ------------------------------------------------------------------ #
    #  Set up parameters
    # ------------------------------------------------------------------ #
    def set_mode(self, mode):
        self.view.mode = mode
        for m, info in self.buttons.items():
            info["button"].setStyleSheet("")  # reset
        if mode in self.buttons:
            color = self.buttons[mode]['color']
            self.buttons[mode]["button"].setStyleSheet(f"""
                QPushButton {{ background-color: {color}; }}
            """)

    def set_group(self):
        group, ok = QInputDialog.getText(self, "Group name", "Enter group name:")
        if ok and group:
            self.current_group = group
            self.group_btn.setText(f"self.column_names[2]: {self.current_group}")

    def set_ground(self, line):
        if self.ground_line_item is not None:
            self.scene.removeItem(self.ground_line_item)
            self.ground_line_item = None
        self.ground_line_item = QGraphicsLineItem(line)
        self.ground_line_item.setPen(QPen(Qt.GlobalColor.red, 2))
        self.scene_group.addToGroup(self.ground_line_item)
        self.scene.addItem(self.ground_line_item)
        self.ground_line = line
        self.recalculate_heights()

    def set_scale(self, line):
        if self.scale_line_item is not None:
            self.scene.removeItem(self.scale_line_item)
            self.scale_line_item = None
        cm, ok = QInputDialog.getDouble(self, "Scale", "Real length (cm)")
        if not ok:
            return
        self.scale_line_item = QGraphicsLineItem(line)
        self.scale_line_item.setPen(QPen(Qt.GlobalColor.green, 2))
        self.scene_group.addToGroup(self.scale_line_item)
        self.scene.addItem(self.scale_line_item)
        self.scale_line = line
        length_px = np.hypot(line.dx(), line.dy())
        self.scale_cm_per_px = cm / length_px
        self.recalculate_heights()

    # ------------------------------------------------------------------ #
    #  Manage flies (points)
    # ------------------------------------------------------------------ #
    def add_fly(self, pos):
        if not self.ground_line or not self.scale_cm_per_px:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Define ground and scale before adding points.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return

        if hasattr(self, "image_width"):
            r = 0.005 * min(self.image_width, self.image_height)
        else:
            r = 4

        point = QGraphicsEllipseItem(pos.x()-r, pos.y()-r, 2*r, 2*r)
        point.setPen(QPen(Qt.GlobalColor.blue))
        self.scene.addItem(point)
        self.fly_points.append({"item": point, "pos": pos, "group": self.current_group})
        self.recalculate_heights()

    def remove_fly(self, item):
        self.scene.removeItem(item)
        self.fly_points = [f for f in self.fly_points if f["item"] != item]
        self.recalculate_heights()

    def recalculate_heights(self):
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
            self.table.setItem(row, 2, QTableWidgetItem(fly["group"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{pos.x():.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{pos.y():.2f}"))

    # ------------------------------------------------------------------ #
    #  Zoom and rotations handling
    # ------------------------------------------------------------------ #
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_rotate_btn_position()

    def update_rotate_btn_position(self):
        margin = 20
        x = self.view.width() - self.rotate_btn.width() - margin
        y = margin
        self.rotate_btn.move(x, y)

    def rotate_image(self):
        if hasattr(self, "pixmap_item"):
            self.pixmap_item.setRotation(self.pixmap_item.rotation() + 90)

    # Rename columns
    def rename_column(self, index):
        current = self.table.horizontalHeaderItem(index).text()
        name, ok = QInputDialog.getText(self, "Rename column", "New name :", text=current)
        if ok and name:
            self.table.setHorizontalHeaderItem(index, QTableWidgetItem(name))
            self.column_names[index] = name
            self.settings.setValue("table/column_names", self.column_names)
            self.group_btn.setText(f"{self.column_names[2]}: {self.current_group}")

    # ------------------------------------------------------------------ #
    #  Help button
    # ------------------------------------------------------------------ #
    def show_help(self):
        help_path = resource_path("doc.md")
        if not os.path.exists(help_path):
            QMessageBox.warning(self, "Erreur", "Fichier doc.md introuvable.")
            return
        with open(help_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        html = markdown.markdown(md_text)
        dialog = QDialog(self)
        dialog.setWindowTitle("Help - Flheight")
        dialog.resize(600, 500)
        layout = QVBoxLayout()
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        dialog.setLayout(layout)
        dialog.exec()

    # ------------------------------------------------------------------ #
    #  Export button
    # ------------------------------------------------------------------ #
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV files (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)

    def export_frame(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export image", self.default_export_name, "Image PNG (*.png)")
        if path:
            self.current_pixmap.save(path, "PNG")

    @staticmethod
    def point_to_line_distance(P, line):
        A = np.array([line.x1(), line.y1()])
        B = np.array([line.x2(), line.y2()])
        P = np.array([P.x(), P.y()])
        d = B - A
        p = A - P
        return np.abs(d[0] * p[1] - d[1] * p[0]) / np.linalg.norm(d)


app = QApplication(sys.argv)
#app.setStyle("Fusion")
window = MainWindow()
window.showMaximized()
sys.exit(app.exec())