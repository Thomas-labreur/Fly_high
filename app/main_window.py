import sys, csv, os, markdown, cv2
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QGraphicsScene, QGraphicsLineItem, QGraphicsEllipseItem, 
    QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget,
    QGraphicsRectItem, QTableWidgetItem, QInputDialog, QToolButton, QMessageBox,
    QDialog, QTextBrowser, QSplitter, QLabel, QMenu,  QFrame, QStackedWidget, 
    QGraphicsTextItem, QLineEdit, QFormLayout, QDialogButtonBox
)
from PyQt6.QtGui import QPixmap, QPen, QFont
from PyQt6.QtCore import Qt, QSettings, QPointF

from video_frame_selector import VideoFrameSelector, CV2_AVAILABLE
from image_view import ImageView
from left_pannel import LeftPanel
from data_processor import DataProcessor

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):

    # All column names in final table order
    ALL_COLUMNS = [
        # Metadata (user)
        "Cohort", "Assay mode", "Genotype", "Condition", "Age (days)", "Sex", "Assay type", "Trial", "ROI name",
        # File info (auto)
        "Filename", "Frame", "FPS",
        # Computed
        "Point ID", "Fly ID", "X (px)", "Y (px)", "Height (cm)", "Source"
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flheight")

        self.settings = QSettings("Config", "Flheight")

        self.scene = QGraphicsScene()
        self.view = ImageView(self.scene)
        self.data_processor = DataProcessor()
        self.view.parent = self

        self.ground_line_item = None
        self.scale_line_item = None
        self.ground_line = None
        self.scale_line = None
        self.scale_cm_per_px = None

        self.fly_points = []
        self.rois = []
        
        self.frozen_rows = [] # liste de dicts {col_index: value} pour les lignes figées
        self.current_video_path = None
        self.current_trial = 0
        self.image_loaded_since_table_load = False

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #bbb;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c8c8c8;
            }
            QPushButton:disabled {
                color: #aaa;
                background-color: #e8e8e8;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                border: none;
                border-right: 1px solid #ccc;
                border-bottom: 1px solid #ccc;
                padding: 4px 6px;
                font-size: 11px;
            }
            QHeaderView::section:hover {
                background-color: #d0d0d0;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 11px;
                border: none;
            }
        """)

        # --- Top toolbar ---
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)

        # File menu
        file_btn = QPushButton("File")
        file_menu = QMenu(self)
        file_menu.addAction("New table", self.new_table)
        file_menu.addAction("Open table", self.open_table)
        file_menu.addAction("Open image", self.open_image)
        action_video = file_menu.addAction("Open video", self.open_video)
        if not CV2_AVAILABLE:
            action_video.setEnabled(False)
        self.new_trial_action = file_menu.addAction("Navigate video", self.reopen_video)
        self.new_trial_action.setEnabled(False)
        file_menu.addSeparator()
        self.export_frame_action = file_menu.addAction("Export image as PNG", self.export_frame)
        self.export_frame_action.setEnabled(False)
        file_menu.addAction("Export table as CSV", self.export_csv)
        file_menu.addAction("Export figure-ready as XLSX", self.export_xlsx)
        file_btn.setMenu(file_menu)
        toolbar_layout.addWidget(file_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #ccc;")
        toolbar_layout.addWidget(sep)

        # Mode buttons
        self.buttons = {}
        modes = [
            ("✥ Nav", "nav", "#888888"),
            ("Ground", "ground", "#e05555"), 
            ("Scale", "scale", "#69fa4f"), 
            ("ROI", "roi", "#f84ef5"),
            ("Fly", "fly", "#00EAFF")
            ]
        for name, mode, color in modes:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, m=mode: self.set_mode(m))
            btn.setEnabled(False)
            toolbar_layout.addWidget(btn)
            self.buttons[mode] = {"button": btn, "color": color, "active_color": color}

        sep_auto = QFrame()
        sep_auto.setFrameShape(QFrame.Shape.VLine)
        sep_auto.setStyleSheet("color: #ccc;")
        toolbar_layout.addWidget(sep_auto)

        self.auto_detect_btn = QPushButton("Automatic detection")
        self.auto_detect_btn.clicked.connect(self.segment_flies_auto)
        self.auto_detect_btn.setEnabled(False)
        toolbar_layout.addWidget(self.auto_detect_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #ccc;")
        toolbar_layout.addWidget(sep2)

        toolbar_layout.addStretch()

        # Help button
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        toolbar_layout.addWidget(help_btn)

        # --- Tab bar (Image / Table) ---
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_image_btn = QPushButton("Image")
        self.tab_table_btn = QPushButton("Table")

        tab_style_active = """
            QPushButton {
                background-color: white;
                border: 1px solid #bbb;
                border-bottom: none;
                border-radius: 0px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 5px 20px;
                font-size: 12px;
                font-weight: bold;
                color: #333;
            }
        """
        tab_style_inactive = """
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #bbb;
                border-bottom: 1px solid #bbb;
                border-radius: 0px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 5px 20px;
                font-size: 12px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """
        self._tab_active_style = tab_style_active
        self._tab_inactive_style = tab_style_inactive

        self.tab_image_btn.setStyleSheet(tab_style_active)
        self.tab_table_btn.setStyleSheet(tab_style_inactive)
        self.tab_image_btn.clicked.connect(lambda: self.switch_tab(0))
        self.tab_table_btn.clicked.connect(lambda: self.switch_tab(1))

        tab_layout.addWidget(self.tab_image_btn)
        tab_layout.addWidget(self.tab_table_btn)
        tab_layout.addStretch()

        # --- Stacked widget (image view / table view) ---
        self.stack = QStackedWidget()

        # Image page
        image_page = QWidget()
        image_page.setStyleSheet("background-color: white; border: 1px solid #bbb;")
        image_layout = QVBoxLayout(image_page)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(self.view)

        # Table page
        table_page = QWidget()
        table_page.setStyleSheet("background-color: white; border: 1px solid #bbb;")
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, len(self.ALL_COLUMNS))
        self.table.setHorizontalHeaderLabels(self.ALL_COLUMNS)
        self.table.horizontalHeader().setMinimumSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { alternate-background-color: #fafafa; }
        """)
        table_layout.addWidget(self.table)

        self.stack.addWidget(image_page)   # index 0
        self.stack.addWidget(table_page)   # index 1

        # Right side = tabs + stack
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addLayout(tab_layout)
        right_layout.addWidget(self.stack)

        # --- Left panel ---
        self.left_panel = LeftPanel()
        self.left_panel.metadata_fields["Trial"].setText("1")

        # --- Main content splitter ---
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.addWidget(self.left_panel)
        content_splitter.addWidget(right_widget)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setHandleWidth(4)

        # --- Status / info bar ---
        self.image_info_label = QLabel("")
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.image_info_label.setStyleSheet("color: #777; font-size: 10px; padding-right: 6px;")
        self.image_info_label.setFixedHeight(18)

        # --- Rotate button (overlay on image view) ---
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

        # --- Root layout ---
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("background-color: #ececec; border-bottom: 1px solid #ccc;")
        toolbar_widget.setLayout(toolbar_layout)
        toolbar_widget.setFixedHeight(38)

        root_layout.addWidget(toolbar_widget)
        root_layout.addWidget(content_splitter)
        root_layout.addWidget(self.image_info_label)

        container = QWidget()
        container.setLayout(root_layout)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------ #
    #  Tab switching
    # ------------------------------------------------------------------ #
    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.tab_image_btn.setStyleSheet(self._tab_active_style)
            self.tab_table_btn.setStyleSheet(self._tab_inactive_style)
        else:
            self.tab_image_btn.setStyleSheet(self._tab_inactive_style)
            self.tab_table_btn.setStyleSheet(self._tab_active_style)

    # ------------------------------------------------------------------ #
    #  Table management
    # ------------------------------------------------------------------ #
    def new_table(self):
        if self.table.rowCount() > 0:
            reply = QMessageBox.question(
                self, "Save before reset",
                "Do you want to export the current table before creating a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.export_csv()
        self.table.setRowCount(0)
        self.image_loaded_since_table_load= False
        self.left_panel.metadata_fields["Trial"].setText(str(1))
        for f in self.fly_points:
            self.scene.removeItem(f["item"])
        self.fly_points = []
        self.frozen_rows = []

    def open_table(self):
        if self.table.rowCount() > 0:
            reply = QMessageBox.question(
                self, "Save before reset",
                "Do you want to export the current table before creating a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.export_csv()

        path, _ = QFileDialog.getOpenFileName(
            self, "Open table", "", "Table files (*.csv *.xlsx)"
        )
        if not path:
            return

        try:
            import pandas as pd
            df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
            # Vérifier que les colonnes correspondent
            missing = [c for c in self.ALL_COLUMNS if c not in df.columns]
            if missing:
                QMessageBox.critical(self, "Format error",
                    f"Missing columns: {', '.join(missing)}")
                return
            df = df[self.ALL_COLUMNS]  # réordonner
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read file:\n{e}")
            return

        # Charger dans la table
        self.table.setRowCount(0)
        for _, row in df.iterrows():
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, col in enumerate(self.ALL_COLUMNS):
                val = "" if pd.isna(row[col]) else str(row[col])
                self.table.setItem(r, c, QTableWidgetItem(val))

        self.frozen_rows = []
        self._freeze_current_rows()
        for f in self.fly_points:
            self.scene.removeItem(f["item"])
        self.fly_points = []
        self.image_loaded_since_table_load = False

        # Remplir le panneau gauche avec les métadonnées de la dernière ligne
        if self.table.rowCount() > 0:
            last_row = self.table.rowCount() - 1
            for field in LeftPanel.METADATA_FIELDS:
                if field in self.ALL_COLUMNS:
                    col_idx = self.ALL_COLUMNS.index(field)
                    item = self.table.item(last_row, col_idx)
                    if item and field not in ["ROI name", "Trial", "Assay mode"]:
                        self.left_panel.metadata_fields[field].setText(item.text())
                    elif field == "Trial":
                            last_trial = int(item.text()) if item and item.text().isdigit() else 0
                            self.left_panel.metadata_fields["Trial"].setText(str(last_trial + 1))
                    elif field == "Assay_mode":
                        self.left_panel.metada_fields["Assay mode"].setCurrentText(item.text())
                    

    # ------------------------------------------------------------------ #
    #  Open image
    # ------------------------------------------------------------------ #
    def open_image(self):
        self._increment_trial_if_needed()
        self.clear_scene()

        path, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._load_pixmap(QPixmap(path))
            filename = os.path.basename(path)
            self.image_info_label.setText(filename)
            self.default_export_name = os.path.splitext(filename)[0]
            self.left_panel.set_file_info(filename=filename, frame="", fps="")
            self.switch_tab(0)

    # ------------------------------------------------------------------ #
    #  Open video
    # ------------------------------------------------------------------ #
    def open_video(self):
        if not CV2_AVAILABLE:
            QMessageBox.warning(self, "Missing module",
                                "opencv-python module is required.\n"
                                "Install with : pip install opencv-python")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Open video", "", "Videos (*.mp4 *.avi *.mov *.mkv)"
        )
        if not path:
            return

        processed = self._get_processed_frames_for_video(path)
        dialog = VideoFrameSelector(path, self, processed_frames=processed)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_pixmap:
            self._increment_trial_if_needed()
            self.clear_scene()
            self._load_pixmap(dialog.selected_pixmap, from_video=True)
            videoname = os.path.basename(path)
            frame = dialog._current_frame_index
            timecode = frame / dialog.fps
            info = f"{videoname} | FPS: {dialog.fps:.2f} | Frame: {frame} ({timecode:.2f}s)"
            self.image_info_label.setText(info)
            self.default_export_name = f"{os.path.splitext(videoname)[0]}_frame{frame}_{timecode:.2f}s"
            self.left_panel.set_file_info(
                filename=videoname,
                frame=str(frame),
                fps=f"{dialog.fps:.2f}"
            )
            # mémoriser la vidéo
            self.current_video_path = path
            self.new_trial_action.setEnabled(True)
            self.switch_tab(0)

    def reopen_video(self):
        if not self.current_video_path:
            return
    
        # Get previous frame number and save it
        processed = self._get_processed_frames_for_video(self.current_video_path)
        dialog = VideoFrameSelector(self.current_video_path, self, processed_frames=processed)

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_pixmap:

            # Sauvegarder l'état avant de vider
            saved_ground_line = self.ground_line
            saved_scale_line = self.scale_line
            saved_scale_cm_per_px = self.scale_cm_per_px
            saved_rois = [(roi.rect(), roi.data(0), roi.data(1)) for roi in self.rois]
            self.view.resetTransform()
            self._freeze_current_rows()

            # Réinitialiser seulement l'image et les annotations, pas les frozen_rows
            self.scene.clear()
            self.ground_line_item = None
            self.scale_line_item = None
            self.ground_line = None
            self.scale_line = None
            self.scale_cm_per_px = None
            self.view.last_line = None
            self.view.temp_line = None
            self.view.start_point = None
            self.fly_points = []
            self.rois = []

            self._load_pixmap(dialog.selected_pixmap, from_video=True)

            # Restaurer le ground
            if saved_ground_line:
                self.ground_line_item = QGraphicsLineItem(saved_ground_line)
                self.ground_line_item.setPen(QPen(Qt.GlobalColor.red, 4))
                self.scene.addItem(self.ground_line_item)
                self.ground_line = saved_ground_line

            # Restaurer le scale
            if saved_scale_line:
                self.scale_line_item = QGraphicsLineItem(saved_scale_line)
                self.scale_line_item.setPen(QPen(Qt.GlobalColor.green, 4))
                self.scene.addItem(self.scale_line_item)
                self.scale_line = saved_scale_line
                self.scale_cm_per_px = saved_scale_cm_per_px

            # Restaurer les ROIs
            for (rect, roi_name, roi_meta) in saved_rois:
                roi = QGraphicsRectItem(rect)
                roi.setPen(QPen(Qt.GlobalColor.magenta, 4))
                roi.setData(0, roi_name)
                roi.setData(1, roi_meta)
                self.scene.addItem(roi)
                label = QGraphicsTextItem(roi_name, roi)
                label.setDefaultTextColor(Qt.GlobalColor.magenta)
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                label.setFont(font)
                label.setPos(rect.x(), rect.y() - label.boundingRect().height())
                self.rois.append(roi)

            videoname = os.path.basename(self.current_video_path)
            frame = dialog._current_frame_index
            timecode = frame / dialog.fps
            info = f"{videoname} | FPS: {dialog.fps:.2f} | Frame: {frame} ({timecode:.2f}s)"
            self.image_info_label.setText(info)
            self.default_export_name = f"{os.path.splitext(videoname)[0]}_frame{frame}_{timecode:.2f}s"
            self.left_panel.set_file_info(
                filename=videoname,
                frame=str(frame),
                fps=f"{dialog.fps:.2f}"
            )
            print(self.image_loaded_since_table_load)
            self._increment_trial_if_needed()
            self.switch_tab(0)

    def _get_processed_frames_for_video(self, video_path):
        filename = os.path.basename(video_path)
        filename_col = self.ALL_COLUMNS.index("Filename")
        frame_col = self.ALL_COLUMNS.index("Frame")
        trial_col = self.ALL_COLUMNS.index("Trial")

        seen = set()
        processed = []

        # Parcourir la table widget
        for row in range(self.table.rowCount()):
            item_filename = self.table.item(row, filename_col)
            if not item_filename or item_filename.text() != filename:
                continue
            item_frame = self.table.item(row, frame_col)
            frame_val = item_frame.text() if item_frame else ""
            item_trial = self.table.item(row, trial_col)
            trial_val = item_trial.text() if item_trial else ""
            if not frame_val or frame_val in seen:
                continue
            seen.add(frame_val)
            processed.append({"frame": int(frame_val), "label": f"Trial {trial_val}"})

        return processed

    def _freeze_current_rows(self):
        """Capture toutes les lignes actuelles de la table en frozen_rows."""
        self.frozen_rows = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data[col] = item.text() if item else ""
            self.frozen_rows.append(row_data)

    def _increment_trial_if_needed(self):
        if self.image_loaded_since_table_load:
            try:
                t = int(self.left_panel.metadata_fields["Trial"].text() or 0)
            except ValueError:
                t = 0
            self.left_panel.metadata_fields["Trial"].setText(str(t + 1))
        self.image_loaded_since_table_load = True

    # ------------------------------------------------------------------ #
    #  Load pixmap
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
        self.auto_detect_btn.setEnabled(True)
        self.set_mode("nav") 
        for mode, info in self.buttons.items():
            info["button"].setEnabled(True)

    # ------------------------------------------------------------------ #
    #  Clear scene
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
        self.rois = []
        self.frozen_rows = []
        self.current_video_path = None
        self.current_trial = 0
        self.new_trial_action.setEnabled(False)
        #self.table.setRowCount(0)
        self._freeze_current_rows()
        self.left_panel.clear_file_info()
        self.auto_detect_btn.setEnabled(False)
        for mode, info in self.buttons.items():
            info["button"].setEnabled(False)
            info["button"].setStyleSheet("")

    # ------------------------------------------------------------------ #
    #  Mode management
    # ------------------------------------------------------------------ #
    def set_mode(self, mode):
        self.view.mode = mode
        if mode == "nav":
            self.view.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.view.setCursor(Qt.CursorShape.ArrowCursor)

        for m, info in self.buttons.items():
            info["button"].setStyleSheet("")

        if mode in self.buttons:
            color = self.buttons[mode]["active_color"]
            self.buttons[mode]["button"].setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: 1px solid #888;
                    border-radius: 4px;
                    padding: 4px 10px;
                }}
            """)

    def set_ground(self, line):
        if self.ground_line_item is not None:
            self.scene.removeItem(self.ground_line_item)
            self.ground_line_item = None
        self.ground_line_item = QGraphicsLineItem(line)
        self.ground_line_item.setPen(QPen(Qt.GlobalColor.red, 4))
        self.scene_group.addToGroup(self.ground_line_item)
        self.scene.addItem(self.ground_line_item)
        self.ground_line = line
        self.recalculate_heights()

    def set_scale(self, line):
        if self.scale_line_item is not None:
            self.scene.removeItem(self.scale_line_item)
            self.scale_line_item = None

        s = QSettings("Config", "Flheight")
        last_scale = float(s.value("scale/last_cm", 0.0))

        cm, ok = QInputDialog.getDouble(self, "Scale", "Real length (cm)", value=last_scale, min=0.0)
        
        if not ok:
            return
        s.setValue("scale/last_cm", cm)
        if not ok:
            return
        self.scale_line_item = QGraphicsLineItem(line)
        self.scale_line_item.setPen(QPen(Qt.GlobalColor.green, 4))
        self.scene_group.addToGroup(self.scale_line_item)
        self.scene.addItem(self.scale_line_item)
        self.scale_line = line
        length_px = np.hypot(line.dx(), line.dy())
        self.scale_cm_per_px = cm / length_px
        self.recalculate_heights()
    
    def add_roi(self, rect):
        dialog = QDialog(self)
        dialog.setWindowTitle("ROI Properties")
        dialog.setStyleSheet("width: 100px")
        layout = QVBoxLayout(dialog)

        info = QLabel(
            "The <b>ROI name</b> is required. All other fields are optional — "
            "if left blank, the value from the left panel will be used."
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 11px; color: #555; margin-bottom: 6px")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(6)
        fields = {}
        field_style = """
            QLineEdit { border: 1px solid #ddd; border-radius: 4px;
                        padding: 3px 6px; font-size: 11px; }
            QLineEdit:focus { border-color: #4169E1; }
        """
        fields_order = ["ROI name"] + [f for f in LeftPanel.METADATA_FIELDS if f not in ("ROI name", "Trial", "Assay mode")]
        for field in fields_order:
            edit = QLineEdit()
            edit.setStyleSheet(field_style)
            if field == "ROI name":
                edit.setPlaceholderText("Required")
            else:
                edit.setPlaceholderText("Leave blank to use panel value")
            form.addRow(QLabel(field), edit)
            fields[field] = edit
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)  # désactivé par défaut
        fields["ROI name"].textChanged.connect(
            lambda text: buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(text.strip()))
        )

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        roi_name = fields["ROI name"].text().strip()

        # Store all metadata overrides on the ROI item
        roi_meta = {}
        for f in fields_order:
            widget = fields[f]
            roi_meta[f] = widget.text().strip()

        roi = QGraphicsRectItem(rect)
        roi.setPen(QPen(Qt.GlobalColor.magenta, 4))
        roi.setData(0, roi_name)
        roi.setData(1, roi_meta)  
        self.scene.addItem(roi)

        label = QGraphicsTextItem(roi_name, roi)
        label.setDefaultTextColor(Qt.GlobalColor.magenta)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        label.setFont(font)
        label.setPos(rect.x(), rect.y() - label.boundingRect().height())

        self.rois.append(roi)
        for fly in self.fly_points:
            if roi.rect().contains(fly["pos"]):
                for field, value in roi_meta.items():
                    if value:  # seulement si renseigné
                        fly["snapshot"][field] = value
                fly["snapshot"]["ROI name"] = roi_name
        self.recalculate_heights()

    def remove_roi(self, item):
        panel_meta = self.left_panel.get_metadata()
        roi_meta = item.data(1) or {}
        roi_name = item.data(0) or ""
        
        for fly in self.fly_points:
            if item.rect().contains(fly["pos"]):
                fly["snapshot"]["ROI name"] = ""
                for field, value in roi_meta.items():
                    if value:  # seulement les champs que ce ROI avait renseignés
                        fly["snapshot"][field] = panel_meta.get(field, "")
        
        self.scene.removeItem(item)
        self.rois = [roi for roi in self.rois if roi != item]
        self.recalculate_heights()

    def _get_roi_for_pos(self, pos):
        panel_meta = self.left_panel.get_metadata()
        for roi in self.rois:
            if roi.rect().contains(pos):
                roi_meta = roi.data(1) or {}
                result = {
                    field: roi_meta.get(field) or panel_meta.get(field, "")
                    for field in LeftPanel.METADATA_FIELDS
                }
                result["Assay mode"] = panel_meta.get("Assay mode", "")
                return result  # ← retourner ici
        return panel_meta


    # ------------------------------------------------------------------ #
    #  Fly points
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

        # Demander le Fly ID si mode "single flies"
        fly_id_user = ""
        assay_mode = self.left_panel.get_metadata().get("Assay mode", "")
        if assay_mode == "single flies":
            fly_id_user = self._ask_fly_id()
            if fly_id_user is None:  # annulé
                return

        r = 0.005 * min(self.image_width, self.image_height) if hasattr(self, "image_width") else 4
        point = QGraphicsEllipseItem(pos.x()-r, pos.y()-r, 2*r, 2*r)
        point.setPen(QPen(Qt.GlobalColor.cyan, 4))
        self.scene.addItem(point)

        snapshot = self._build_row_snapshot(pos, source="manual")
        snapshot["Fly ID"] = fly_id_user
        self.fly_points.append({"item": point, "pos": pos, "source": "manual", "snapshot": snapshot})
        self.recalculate_heights()

    def remove_fly(self, item):
        self.scene.removeItem(item)
        self.fly_points = [f for f in self.fly_points if f["item"] != item]
        self.recalculate_heights()

    def _ask_fly_id(self):
        """Dialog pour choisir ou créer un Fly ID."""
        from PyQt6.QtWidgets import QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox

        # Collecter les Fly ID déjà présents dans la table
        fly_id_col = self.ALL_COLUMNS.index("Fly ID")
        existing_ids = []
        seen = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, fly_id_col)
            if item and item.text().strip() and item.text().strip() not in seen:
                existing_ids.append(item.text().strip())
                seen.add(item.text().strip())

        dialog = QDialog(self)
        dialog.setWindowTitle("Fly ID")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Select an existing Fly ID or type a new one:"))

        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(existing_ids)
        combo.setCurrentText("")  # champ vide par défaut
        combo.lineEdit().setPlaceholderText("e.g. fly_01")
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        return combo.currentText().strip()

    def recalculate_heights(self):
        self.table.setRowCount(0)

        # Restaurer les lignes figées
        for row_data in self.frozen_rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in row_data.items():
                self.table.setItem(row, col, QTableWidgetItem(value))

        for idx, fly in enumerate(self.fly_points):
            pos = fly["pos"]
            snap = fly.get("snapshot", {})
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Colonnes dont la valeur est figée au snapshot
            frozen_fields = [
                "Cohort", "Assay mode", "Genotype", "Condition", "Age (days)", 
                "Sex", "Assay type", "Trial", "Filename", "Frame", "FPS"
            ]

            for field in frozen_fields:
                col_idx = self.ALL_COLUMNS.index(field)
                self.table.setItem(row, col_idx, QTableWidgetItem(snap.get(field, "")))

            # ROI name
            roi_col = self.ALL_COLUMNS.index("ROI name")
            self.table.setItem(row, roi_col, QTableWidgetItem(snap.get("ROI name", "")))

            if self.ground_line and self.scale_cm_per_px:
                height_px = self.point_to_line_distance(pos, self.ground_line)
                height_cm = f"{height_px * self.scale_cm_per_px:.2f}"
            else:
                height_cm = ""

            # Fly ID, X, Y, Height, Source
            for field, value in [
                ("Point ID",    str(idx)),
                ("Fly ID",      snap.get("Fly ID", "")),  # user input
                ("X (px)",      f"{pos.x():.2f}"),
                ("Y (px)",      f"{pos.y():.2f}"),
                ("Height (cm)", height_cm),
                ("Source",      snap.get("Source", fly.get("source", ""))),
            ]:
                self.table.setItem(row, self.ALL_COLUMNS.index(field), QTableWidgetItem(value))

    def segment_flies_auto(self):
        if not self.rois:
            QMessageBox.warning(self, "No ROI", "Draw at least one ROI first.")
            return
        if not hasattr(self, "current_pixmap"):
            QMessageBox.warning(self, "No image", "Open an image first.")
            return
        if not self.ground_line or not self.scale_cm_per_px:
            QMessageBox.warning(self, "Missing setup",
                                "Define ground and scale before auto-detection.")
            return

        # Convertir le QPixmap en tableau numpy BGR
        qimg = self.current_pixmap.toImage().convertToFormat(
            self.current_pixmap.toImage().Format.Format_RGB888
        )
        width, height = qimg.width(), qimg.height()
        ptr = qimg.bits()
        ptr.setsize(height * width * 3)
        frame_rgb = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 3))
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)

        # Paramètres (tu pourras les exposer dans l'UI plus tard)
        thr = 80
        min_area = 10
        max_area = 500
        kernel = np.ones((3, 3), np.uint8)

        # Supprimer les détections auto précédentes
        self.fly_points = [f for f in self.fly_points if not f.get("auto")]
        # Redessiner pour nettoyer les anciens cercles auto
        # (on garde les items manuels, on retire les auto)
        for item in self.scene.items():
            if isinstance(item, QGraphicsEllipseItem):
                # Les items auto sont stockés avec un flag, on les retire
                pass  # géré ci-dessous via fly_points

        # Plus simple : retirer du scene tous les ellipses marquées "auto"
        for f in list(self.fly_points):
            if f.get("auto"):
                self.scene.removeItem(f["item"])
        self.fly_points = [f for f in self.fly_points if not f.get("auto")]

        count = 0
        r = 0.005 * min(self.image_width, self.image_height)

        for roi in self.rois:
            rect = roi.rect()
            x1, y1 = int(rect.x()), int(rect.y())
            x2, y2 = int(rect.x() + rect.width()), int(rect.y() + rect.height())
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            crop = gray[y1:y2, x1:x2]
            mask = (crop < thr).astype(np.uint8) * 255
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            num, _, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

            for i in range(1, num):
                area = stats[i, cv2.CC_STAT_AREA]
                if area < min_area or area > max_area:
                    continue
                cx, cy = centroids[i]
                gx, gy = x1 + float(cx), y1 + float(cy)

                pos = QPointF(gx, gy)
                point = QGraphicsEllipseItem(gx - r, gy - r, 2 * r, 2 * r)
                point.setPen(QPen(Qt.GlobalColor.blue, 4))
                self.scene.addItem(point)
                snapshot = self._build_row_snapshot(pos, source="auto")
                snapshot["Assay mode"] = "group tubes"
                self.fly_points.append({"item": point, "pos": pos, 
                                        "source": "auto", "snapshot": snapshot, 
                                        "auto": True})
                count += 1

        self.recalculate_heights()
        QMessageBox.information(self, "Detection done",
                                f"{count} fly(ies) detected automatically.")
        
    def _build_row_snapshot(self, pos, source="manual"):
        """Capture l'état complet d'une ligne au moment de la création du point."""
        roi_meta = self._get_roi_for_pos(pos)
        file_meta = self.left_panel.get_metadata()
        return {
            # Metadata utilisateur (depuis ROI ou panneau gauche)
            "Cohort":       roi_meta.get("Cohort", ""),
            "Assay mode":   roi_meta.get("Assay mode", ""),
            "Genotype":     roi_meta.get("Genotype", ""),
            "Condition":    roi_meta.get("Condition", ""),
            "Age (days)":   roi_meta.get("Age (days)", ""),
            "Sex":          roi_meta.get("Sex", ""),
            "Assay type":   roi_meta.get("Assay type", ""),
            "Trial":        roi_meta.get("Trial", ""),
            "ROI name": roi_meta.get("ROI name", ""),
            # File info (figé)
            "Filename":     file_meta.get("Filename", ""),
            "Frame":        file_meta.get("Frame", ""),
            "FPS":          file_meta.get("FPS", ""),
            # Source
            "Fly ID":       "",
            "Source":       source,
        }

    # ------------------------------------------------------------------ #
    #  Zoom / rotation
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

    # ------------------------------------------------------------------ #
    #  Help
    # ------------------------------------------------------------------ #
    def show_help(self):
        help_path = resource_path("doc.md")
        if not os.path.exists(help_path):
            QMessageBox.warning(self, "Error", "doc.md file not found.")
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
    #  Export
    # ------------------------------------------------------------------ #
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", getattr(self, "default_export_name", ""), "CSV files (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            for row in range(self.table.rowCount()):
                row_data = [
                    (self.table.item(row, col).text() if self.table.item(row, col) else "")
                    for col in range(self.table.columnCount())
                ]
                writer.writerow(row_data)

    def export_frame(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export image",
            getattr(self, "default_export_name", ""),
            "Image PNG (*.png)"
        )
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
    
    def export_xlsx(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Empty table", "No data to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export XLSX", getattr(self, "default_export_name", ""), "Excel files (*.xlsx)"
        )
        if not path:
            return
        try:
            sheets = self.data_processor.all_sheets(self.table, self.ALL_COLUMNS)
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                for sheet_name, df in sheets.items():
                    if df is not None and not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            QMessageBox.information(self, "Export done", f"Exported {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export error", str(e))
