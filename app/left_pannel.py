from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget,  QLineEdit, QFrame, 
    QScrollArea, QFormLayout, QGroupBox, QLabel, QComboBox,
    QSlider, QHBoxLayout, QSpinBox, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIntValidator

class LeftPanel(QWidget):
    """Left panel with metadata fields and file info (read-only)."""

    # Fields the user fills in manually
    METADATA_FIELDS = ["Cohort", "Assay mode", "Genotype", "Condition", "Age (days)", "Sex", "Assay type", "Image ID", "Trial", "ROI name", "Fly ID"]
    # Fields filled automatically from the loaded file
    FILE_FIELDS = ["Filename", "Frame", "FPS", "Resolution"]

    def __init__(self, parent=None, on_transform_change=None, on_metadata_change=None):
        self._on_metadata_change = on_metadata_change
        self._on_transform_change = on_transform_change
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        inner.setStyleSheet("background-color: #f5f5f5;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(12)

        # --- Metadata group ---
        meta_group = QGroupBox("Metadata (default)")
        meta_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 8px;
                background-color: white;
                padding: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #333;
            }
        """)
        meta_form = QFormLayout(meta_group)
        meta_form.setSpacing(6)
        meta_form.setContentsMargins(8, 16, 8, 8)

        self.metadata_fields = {}
        field_style = """
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 3px 6px;
                background: white;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #4169E1;
            }
        """
        readonly_style = """
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 3px 6px;
                background: #f0f0f0;
                color: #666;
                font-size: 11px;
            }
        """
        label_style = "font-size: 11px; color: #555; font-weight: normal;"

        for field in self.METADATA_FIELDS:

            if field == "Assay mode":
                combo = QComboBox()
                combo.addItems(["group tubes", "single flies"])
                combo.setStyleSheet("font-size: 11px;")
                lbl = QLabel(field)
                lbl.setStyleSheet(label_style)
                meta_form.addRow(lbl, combo)
                self.metadata_fields[field] = combo
            
            else:
                edit = QLineEdit()
                edit.setPlaceholderText(f"{field}…")
                if field in ("ROI name", "Fly ID"):
                    f = field.split(" ")[0]
                    edit.setPlaceholderText(f+"_1, "+f+"_2, ...")
                edit.setStyleSheet(field_style)
                if field in ("Image ID", "Trial", "Age (days)"):
                    edit.setValidator(QIntValidator())
                lbl = QLabel(field)
                lbl.setStyleSheet(label_style)
                meta_form.addRow(lbl, edit)
                self.metadata_fields[field] = edit
                if field == "Image ID":
                    edit.setReadOnly(True)
                    edit.setStyleSheet(readonly_style)  

        inner_layout.addWidget(meta_group)

        # --- File info group ---
        file_group = QGroupBox("File info")
        file_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 8px;
                background-color: white;
                padding: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #333;
            }
        """)
        file_form = QFormLayout(file_group)
        file_form.setSpacing(6)
        file_form.setContentsMargins(8, 16, 8, 8)

        self.file_fields = {}
        for field in self.FILE_FIELDS:
            edit = QLineEdit()
            edit.setReadOnly(True)
            edit.setPlaceholderText("—")
            edit.setStyleSheet(readonly_style)
            lbl = QLabel(field)
            lbl.setStyleSheet(label_style)
            file_form.addRow(lbl, edit)
            self.file_fields[field] = edit

        inner_layout.addWidget(file_group)

        # --- Image transforms group ---
        transform_group = QGroupBox("Image transform")
        transform_form = QFormLayout(transform_group)

        self.flip_checkbox = QCheckBox("Flip horizontally")
        self.flip_checkbox.setStyleSheet("font-size: 11px;")
        self.flip_checkbox.stateChanged.connect(self._trigger_transform)
        transform_form.addRow(self.flip_checkbox)

        rotate_layout = QHBoxLayout()
        self.rotate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.setValue(0)
        self.rotation_label = QLabel("0°")
        self.rotation_label.setStyleSheet("font-size: 11px; color: #555;")
        rotate_layout.addWidget(self.rotate_slider)
        rotate_layout.addWidget(self.rotation_label)
        self.rotation_title_label = QLabel("Rotation")
        transform_form.addRow(self.rotation_title_label, rotate_layout)
        self._rotation = 0
        self.rotate_slider.valueChanged.connect(self._on_rotate)

        inner_layout.addWidget(transform_group)

        # --- Detection parameters group ---
        detect_group = QGroupBox("Auto-detection")
        detect_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 8px;
                background-color: white;
                padding: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #333;
            }
        """)
        detect_form = QFormLayout(detect_group)
        detect_form.setSpacing(6)
        detect_form.setContentsMargins(8, 16, 8, 8)

        # Threshold slider
        thr_layout = QHBoxLayout()
        self.thr_slider = QSlider(Qt.Orientation.Horizontal)
        self.thr_slider.setRange(0, 255)
        self.thr_slider.setValue(80)
        self.thr_label = QLabel("80")
        self.thr_label.setFixedWidth(28)
        self.thr_label.setStyleSheet("font-size: 11px; color: #555;")
        self.thr_slider.valueChanged.connect(
            lambda v: self.thr_label.setText(str(v))
        )
        self.thr_slider.valueChanged.connect(
            lambda v: self._save_field("detection/threshold", str(v))
        )
        thr_layout.addWidget(self.thr_slider)
        thr_layout.addWidget(self.thr_label)
        lbl_thr = QLabel("Threshold")
        lbl_thr.setStyleSheet(label_style)
        detect_form.addRow(lbl_thr, thr_layout)

        # Min area spinbox
        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(1, 10000)
        self.min_area_spin.setValue(10)
        self.min_area_spin.setSuffix(" px²")
        self.min_area_spin.setStyleSheet("font-size: 11px;")
        self.min_area_spin.valueChanged.connect(
            lambda v: self._save_field("detection/threshold", str(v))
        )
        lbl_min = QLabel("Min area")
        lbl_min.setStyleSheet(label_style)
        detect_form.addRow(lbl_min, self.min_area_spin)

        # Max area spinbox
        self.max_area_spin = QSpinBox()
        self.max_area_spin.setRange(1, 100000)
        self.max_area_spin.setValue(500)
        self.max_area_spin.setSuffix(" px²")
        self.max_area_spin.setStyleSheet("font-size: 11px;")
        self.max_area_spin.valueChanged.connect(
            lambda v: self._save_field("detection/threshold", str(v))
        )
        lbl_max = QLabel("Max area")
        lbl_max.setStyleSheet(label_style)
        detect_form.addRow(lbl_max, self.max_area_spin)

        inner_layout.addWidget(detect_group)


        inner_layout.addStretch()

        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._load_settings()
        for field, edit in self.metadata_fields.items():
            if field not in ["Image ID", "Assay mode"]:
                edit.textChanged.connect(lambda text, f=field: self._on_field_changed(f, text))
            elif field == "Assay mode":
                edit.currentTextChanged.connect(lambda text, f=field: self._on_field_changed(f, text))

    def _on_field_changed(self, field, value):
        self._save_field(field, value)
        if self._on_metadata_change:
            self._on_metadata_change(field, value)

    def _save_field(self, field, value):
        s = QSettings("Config", "Flheight")
        s.setValue(f"metadata/{field}", value)

    def _load_settings(self):
        s = QSettings("Config", "Flheight")
        for field, edit in self.metadata_fields.items():
            if field not in ["Image ID", "Assay mode"]:
                val = s.value(f"metadata/{field}", "")
                edit.setText(val)
            elif field == "Assay mode":
                val = s.value(f"metadata/{field}", "")
                edit.setCurrentText(val)
        self.thr_slider.setValue(int(s.value("detection/threshold", 80)))
        self.min_area_spin.setValue(int(s.value("detection/min_area", 10)))
        self.max_area_spin.setValue(int(s.value("detection/max_area", 500)))

    def _on_rotate(self):
        self._rotation = self.rotate_slider.value()
        self.rotation_label.setText(f"{self._rotation}°")
        self._trigger_transform()

    def _trigger_transform(self, *args):
        if self._on_transform_change:
            self._on_transform_change()
            
    def get_name_list(self, field):
        """Retourne la liste des noms pour un champ CSV."""
        text = self.metadata_fields[field].text()
        return [s.strip() for s in text.split(",") if s.strip()]
    
    def get_metadata(self):
        """Returns a dict of all metadata values (user-entered + file info)."""
        data = {}
        for field, widget in self.metadata_fields.items():
            from PyQt6.QtWidgets import QComboBox
            data[field] = widget.currentText() if isinstance(widget, QComboBox) else widget.text()
        for field, edit in self.file_fields.items():
            data[field] = edit.text()
        return data

    def get_rotation(self): return self._rotation
    def get_flip(self): return self.flip_checkbox.isChecked()
    
    def get_detection_params(self):
        return {
            "threshold": self.thr_slider.value(),
            "min_area":  self.min_area_spin.value(),
            "max_area":  self.max_area_spin.value(),
        }

    def set_file_info(self, filename="", frame="", fps="", resolution=""):
        self.file_fields["Filename"].setText(filename)
        self.file_fields["Filename"].setToolTip(filename)  # ← ajouter
        self.file_fields["Filename"].home(False)            # ← repositionne au début
        self.file_fields["Frame"].setText(frame)
        self.file_fields["FPS"].setText(fps)
        self.file_fields["Resolution"].setText(resolution)

    def clear_file_info(self):
        for edit in self.file_fields.values():
            edit.setText("")