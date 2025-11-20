from __future__ import annotations
import time
import math
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QHBoxLayout,
    QLabel, 
    QPushButton,
    QComboBox,
    QSlider,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtSvgWidgets import QSvgWidget


class TestModePage(QWidget):
    """
    A test mode that shows live gesture classification and continous strength (scalar) value
    """
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)

        #Title
        title = QLabel("Test Mode")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 700; margin: 8px;")

        # ComboBox mode selector
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Discrete", "Continuous"])
        self.mode_selector.setFixedWidth(180)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)
        self.mode_selector.setStyleSheet("font-size: 14px;")
        self.mode_selector.setFocusPolicy(Qt.ClickFocus)

        # Discrete view container
        self.discrete_container = QWidget()
        discrete_layout = QVBoxLayout()
        self.current_label = QLabel("Current Gesture: REST")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setStyleSheet("font-size: 20px; font-weight: 600; margin: 12px;")

        hint = QLabel("Press R / P / S. If idle for 3 seconds -> REST")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #777; margin-bottom: 4px;")

        discrete_layout.addWidget(self.current_label)
        discrete_layout.addWidget(hint)
        
        # SVG Gesture Icon Setup
        self._gesture_icon_dir = (
            Path(__file__).resolve().parent.parent / "assets" / "gestures"
        )

        self.gesture_icon = QSvgWidget()
        self.gesture_icon.setFixedSize(160, 160)

        # Load the initial REST icon
        rest_icon = self._gesture_icon_dir / "rest.svg"
        if rest_icon.exists():
            self.gesture_icon.load(str(rest_icon))

        # You know we centering that icon
        discrete_layout.addWidget(self.gesture_icon, alignment=Qt.AlignCenter)
        self.discrete_container.setLayout(discrete_layout)

        # Continuous View Container
        self.continuous_container = QWidget()
        cont_layout = QVBoxLayout()
        cont_title = QLabel("Continuous Scalar View")
        cont_title.setAlignment(Qt.AlignCenter)
        cont_title.setStyleSheet("font-size: 16px; color: #666; margin: 8px;")
        
        # Vertical Slider showing the strength scalar [-1, 1]
        self.cont_slider = QSlider(Qt.Vertical)
        self.cont_slider.setMinimum(-100)
        self.cont_slider.setMaximum(100)
        self.cont_slider.setValue(0)
        self.cont_slider.setTickInterval(25)
        self.cont_slider.setTickPosition(QSlider.TicksBothSides)
        self.cont_slider.setEnabled(False)

        # Numeric Value Label
        self.cont_value_label = QLabel("Value = +0.00")
        self.cont_value_label.setAlignment(Qt.AlignCenter)
        self.cont_value_label.setStyleSheet("font-size: 16px; margin: 8px;")

        # Center Slider
        slider_row = QHBoxLayout()
        slider_row.addStretch()
        slider_row.addWidget(self.cont_slider)
        slider_row.addStretch()

        # Continuous Layout
        cont_layout.addWidget(cont_title)
        cont_layout.addLayout(slider_row)
        cont_layout.addWidget(self.cont_value_label)
        self.continuous_container.setLayout(cont_layout)
        self.continuous_container.setVisible(False)

        # Back Button
        back_btn = QPushButton("Back")
        back_btn.setFixedHeight(36)
        back_btn.clicked.connect(on_back_clicked)

        # Main Layout
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.mode_selector)
        layout.addSpacing(12)
        layout.addWidget(self.discrete_container)
        layout.addWidget(self.continuous_container)
        layout.addStretch()
        layout.addWidget(back_btn)
        layout.addStretch()
        self.setLayout(layout)

        #-----------------------------------------------------------
        # Gesture state handler
        #-----------------------------------------------------------

        self._current_gesture = "REST"
        self._last_change_time: float | None = None
        self._timeout_s = 2.0 # 3 Seconds before returning to REST

        # Timer for REST timeout
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._check_timeout)
        self._timer.start()

        #----------------------------------------------------------
        # Continuous State handler 
        #----------------------------------------------------------

        self._cont_user_value = 0.0
        self._cont_velocity = 0.0
        self._cont_up_pressed = False
        self._cont_down_pressed = False 
        self._cont_accel = 2.2
        self._cont_damping = 3.0
        self._cont_vmax = 3.0
        self._cont_center_pull = 0.5
        self._cont_last_tick = time.perf_counter()

        # Physics Timer
        self._cont_timer = QTimer(self)
        self._cont_timer.setInterval(20)
        self._cont_timer.timeout.connect(self._cont_tick)
        self._cont_timer.start()

        # Capture keys at page level
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    #---------------------------------------------------------
    # Mode Switching Logic
    #---------------------------------------------------------
    def _on_mode_changed(self, text: str):
        """
        Show/hide containers based on combo selection 
        """
        if text == "Discrete":
            self.discrete_container.setVisible(True)
            self.continuous_container.setVisible(False)
            self.setFocus()
        elif text == "Continuous":
            self.discrete_container.setVisible(False)
            self.continuous_container.setVisible(True)
            self.setFocus()

    #---------------------------------------------------------
    # Key Handling 
    #---------------------------------------------------------

    def keyPressEvent(self, event):
        ch = event.text().lower()
        key = event.key()

        # Discrete Control
        if ch == "r":
            self._set_gesture("ROCK")
        elif ch == "p":
            self._set_gesture("PAPER")
        elif ch == "s":
            self._set_gesture("SCISSORS") 

        # Continuous Control
        if key == Qt.Key_Up:
            self._cont_up_pressed = True
        elif key == Qt.Key_Down:
            self._cont_down_pressed = True

    def keyReleaseEvent(self, event):
        key = event.key()

        if key == Qt.Key_Up:
            self._cont_up_pressed = False
        elif key == Qt.Key_Down:
            self._cont_down_pressed = False
    
    #----------------------------------------------------------
    # Helpers
    #----------------------------------------------------------

    def _set_gesture(self, gesture: str):
        """
        Update the current gesture and reset the timer
        """
        self._current_gesture = gesture
        self._last_change_time = time.perf_counter()
        self.current_label.setText(f"Current Gesture: {gesture}")
        self._update_gesture_icon(gesture)

    def _update_gesture_icon(self, gesture: str):
        """
        Loads the correct svg file
        """
        if not hasattr(self, "_gesture_icon_dir"):
            return
        
        filename = gesture.lower() + ".svg"
        svg_path = self._gesture_icon_dir / filename

        # If the icon doesn't exist fall back to rest
        if not svg_path.exists():
            svg_path = self._gesture_icon_dir / "rest.svg"
            if not svg_path.exists():
                return
            
        self.gesture_icon.load(str(svg_path))
        self.gesture_icon.update()

    def _check_timeout(self):
        """
        If no inputs are received for 5 seconds, return REST
        """

        if self._current_gesture == "REST":
            return
        if self._last_change_time is None:
            return
        
        now = time.perf_counter()
        if (now - self._last_change_time) >= self._timeout_s:
            # go back to REST
            self._current_gesture = "REST"
            self._last_change_time = None
            self.current_label.setText("Current Gesture: REST")
            self._update_gesture_icon("REST")

    def _cont_tick(self):
        """
        Update continuous scalar value using keyboard physics.
        Print scalar value and reflect it on the slider
        functions the same as trackerMode
        """

        now = time.perf_counter()
        dt = max(0.0, now - self._cont_last_tick)
        self._cont_last_tick = now

        if dt <= 0.0:
            return
        
        # Input force
        force = (1.0 if self._cont_up_pressed else 0.0) - (1.0 if self._cont_down_pressed else 0.0)

        # Acceleration with damping
        self._cont_velocity += self._cont_accel * force * dt

        # Clamp Velocity to vmax
        if self._cont_velocity > self._cont_vmax:
            self._cont_velocity = self._cont_vmax
        elif self._cont_velocity < -self._cont_vmax:
            self._cont_velocity = self._cont_vmax

        # Apply Damping
        self._cont_velocity -= self._cont_damping * self._cont_velocity * dt

        # Integrate into user_value and clamp scalar [-1, 1]
        self._cont_user_value += self._cont_velocity * dt

        if force == 0.0 and abs(self._cont_user_value) > 1e-4:
            direction = math.copysign(1.0, self._cont_user_value)
            self._cont_user_value -= self._cont_center_pull * direction * dt

        if self._cont_user_value > 1.0:
            self._cont_user_value = 1.0
            self._cont_velocity = 0.0
        elif self._cont_user_value < -1.0:
            self._cont_user_value = -1.0
            self._cont_velocity = 0.0

        if abs(self._cont_user_value) < 1e-2 and force == 0.0:
            self._cont_user_value = 0.0
            self._cont_velocity = 0.0

        # Update Slider
        slider_val = int(round(self._cont_user_value * 100.0))
        self.cont_slider.setValue(slider_val)
        self.cont_value_label.setText(f"Value = {self._cont_user_value:+.2f}")
        