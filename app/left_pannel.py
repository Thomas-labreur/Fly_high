from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget,  QLineEdit, QFrame, 
    QScrollArea, QFormLayout, QGroupBox, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIntValidator

class LeftPanel(QWidget):
    """Left panel with metadata fields and file info (read-only)."""

    # Fields the user fills in manually
    METADATA_FIELDS = ["Cohort", "Assay mode", "Genotype", "Condition", "Age (days)", "Sex", "Assay type", "Trial", "ROI name"]
    # Fields filled automatically from the loaded file
    FILE_FIELDS = ["Filename", "Frame", "FPS"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
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

        hint = QLabel(
            "Values here are used as defaults for flies outside of a ROI. "
            "Each ROI can override them individually."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 10px; color: #888; padding: 2px 4px 6px 4px;")
        meta_form.addRow(hint)

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
                edit.setStyleSheet(field_style)
                if field in ("Trial", "Age (days)"):
                    edit.setValidator(QIntValidator())
                lbl = QLabel(field)
                lbl.setStyleSheet(label_style)
                meta_form.addRow(lbl, edit)
                self.metadata_fields[field] = edit
                if field == "Trial":
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
        inner_layout.addStretch()

        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._load_settings()
        for field, edit in self.metadata_fields.items():
            if field not in ["Trial", "Assay mode"]:
                edit.textChanged.connect(lambda text, f=field: self._save_field(f, text))
            elif field=="Assay mode":
                edit.currentTextChanged.connect(lambda text, f=field: self._save_field(f, text))

    def _save_field(self, field, value):
        s = QSettings("Config", "Flheight")
        s.setValue(f"metadata/{field}", value)

    def _load_settings(self):
        s = QSettings("Config", "Flheight")
        for field, edit in self.metadata_fields.items():
            if field not in ["Trial", "Assay mode"]:
                val = s.value(f"metadata/{field}", "")
                edit.setText(val)
            elif field == "Assay mode":
                val = s.value(f"metadata/{field}", "")
                edit.setCurrentText(val)
            
    def get_metadata(self):
        """Returns a dict of all metadata values (user-entered + file info)."""
        data = {}
        for field, widget in self.metadata_fields.items():
            from PyQt6.QtWidgets import QComboBox
            data[field] = widget.currentText() if isinstance(widget, QComboBox) else widget.text()
        for field, edit in self.file_fields.items():
            data[field] = edit.text()
        return data

    def set_file_info(self, filename="", frame="", fps=""):
        self.file_fields["Filename"].setText(filename)
        self.file_fields["Filename"].setToolTip(filename)  # ← ajouter
        self.file_fields["Filename"].home(False)            # ← repositionne au début
        self.file_fields["Frame"].setText(frame)
        self.file_fields["FPS"].setText(fps)

    def clear_file_info(self):
        for edit in self.file_fields.values():
            edit.setText("")