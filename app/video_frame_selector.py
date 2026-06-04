from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QInputDialog,
    QDialog, QSlider, QLabel, QSpinBox, QDialogButtonBox, QComboBox,
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, QSettings

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class TrialSlider(QWidget):
    def __init__(self, total_frames, processed_frames, parent=None):
        super().__init__(parent)
        self.total_frames = total_frames
        self.processed_frames = processed_frames
        self.setMinimumHeight(44)

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, total_frames - 1))
        self.slider.setValue(0)
        # Laisser de la place en bas pour les marqueurs
        self.slider.setGeometry(0, 0, self.width(), 22)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.slider.setGeometry(0, 0, self.width(), 22)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QFontMetrics
        super().paintEvent(event)
        if not self.processed_frames or self.total_frames <= 1:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Zone utile du slider (les curseurs Qt ont des marges internes ~8px de chaque côté)
        margin = 8
        usable_width = self.width() - 2 * margin

        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        fm = QFontMetrics(font)

        for entry in self.processed_frames:
            frame = entry["frame"]
            label = entry["label"]
            ratio = frame / max(1, self.total_frames - 1)
            x = int(margin + ratio * usable_width)

            # Barre magenta
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#f84ef5"))
            painter.drawRect(x - 1, 24, 3, 10)

            # Label
            painter.setPen(QColor("#f84ef5"))
            text_width = fm.horizontalAdvance(label)
            painter.drawText(x - text_width // 2, 44, label)

        painter.end()

class VideoFrameSelector(QDialog):
    def __init__(self, video_path, parent=None, processed_frames=None):
        super().__init__(parent)
        self.setWindowTitle("Frame selection")
        self.resize(900, 620)
        self.video_path = video_path
        self.selected_pixmap = None

        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.play_speed = 1.0
        self.processed_frames = processed_frames or []

        layout = QVBoxLayout(self)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(400)
        self.preview_label.setStyleSheet("background-color: #111; border-radius: 6px;")
        layout.addWidget(self.preview_label)

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

        self.slider_container = TrialSlider(self.total_frames, self.processed_frames, self)
        self.slider = self.slider_container.slider
        layout.addWidget(self.slider_container)
        self.slider.valueChanged.connect(self.on_slider_changed)

        self.play_button = QPushButton("▶ Play")
        self.play_button.setCheckable(True)
        self.play_start_time = None
        self.play_start_frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.play_button.clicked.connect(self.toggle_play)

        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["x1", "x0.75", "x0.5", "x0.25"])
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)

        play_layout = QHBoxLayout()
        play_layout.addWidget(QLabel("Speed :"))
        play_layout.addWidget(self.speed_combo)
        play_layout.addStretch()
        play_layout.addWidget(self.play_button)
        play_layout.addStretch()
        layout.addLayout(play_layout)
        right_spacer = QWidget()
        right_spacer.setFixedWidth(self.speed_combo.sizeHint().width() + QLabel("Speed :").sizeHint().width())
        play_layout.addWidget(right_spacer)

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

        # Go to button
        self.settings = QSettings("MonApp", "VideoFrameSelector")
        self.goto_seconds = self.settings.value("goto_seconds", 4.0, type=float)
        btn_goto = QPushButton(f"Jump +{self.goto_seconds:.0f}s")
        self.btn_goto = btn_goto
        btn_goto.clicked.connect(self.goto_jump)
        btn_goto_setup = QPushButton("⚙")
        btn_goto_setup.setFixedWidth(45)
        btn_goto_setup.setToolTip("Set jump duration")
        btn_goto_setup.clicked.connect(self.goto_setup_dialog)

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
        nav_layout.addWidget(btn_goto_setup)
        layout.addLayout(nav_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._current_frame_index = 0
        self._updating = False
        self.show_frame(0)

    def show_frame(self, index):
        index = max(0, min(index, self.total_frames - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.cap.read()
        if not ret:
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        preview_size = self.preview_label.size()
        scaled = pixmap.scaled(preview_size, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.FastTransformation)
        self.preview_label.setPixmap(scaled)
        self.selected_pixmap = pixmap
        self._current_frame_index = index
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

    def toggle_play(self, checked):
        if checked:
            self.play_button.setText("⏸ Pause")
            self._playing = True
            self.timer.start(int(1000 / (self.fps * self.play_speed)))
        else:
            self.play_button.setText("▶ Play")
            self._playing = False
            self.timer.stop()

    def next_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.play_button.setChecked(False)
            self.toggle_play(False)
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        qimg = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.selected_pixmap = pixmap
        self._current_frame_index = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
        scaled = pixmap.scaled(self.preview_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.FastTransformation)
        self.preview_label.setPixmap(scaled)
        # Sync slider/spinbox sans retriggerer show_frame
        self._updating = True
        self.slider.setValue(self._current_frame_index)
        self.spinbox.setValue(self._current_frame_index)
        self._updating = False
        time_s = self._current_frame_index / self.fps
        self.frame_info_label.setText(f"Frame : {self._current_frame_index} / {self.total_frames - 1}")
        self.time_info_label.setText(f"Time : {time_s:.2f} s")

    def _on_speed_changed(self, text):
        self.play_speed = float(text[1:])
        if self.timer.isActive():
            self.timer.setInterval(int(1000 / (self.fps * self.play_speed)))

    def on_spinbox_changed(self, value):
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(value)
        self.show_frame(value)
        self._updating = False

    def goto_jump(self):
        delta = int(round(self.goto_seconds * self.fps))
        self.step_frames(delta)

    def goto_setup_dialog(self):
        max_s = (self.total_frames - 1) / self.fps if self.fps else 99999
        val, ok = QInputDialog.getDouble(
            self, "Jump duration", "Seconds :",
            self.goto_seconds, 0.1, max_s, 1
        )
        if ok:
            self.goto_seconds = val
            self.settings.setValue("goto_seconds", val)
            self.btn_goto.setText(f"Jump +{val:.0f}s")


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
        self.show_frame(self._current_frame_index)
