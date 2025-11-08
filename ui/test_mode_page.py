from __future__ import annotations
import time

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer


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

        subtitle = QLabel("Live input sandbox - Discrete view")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; coloc: #555; margin-bottom: 6px;")

        # Discrete Gesture Display
        self.current_label = QLabel("Current Gesture: REST")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setStyleSheet("font-size: 20px; font-weight: 600; margin: 12px;")

        hint = QLabel("Press R / P / S. If idle for 5 seconds -> REST")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #777; margin-bottom: 4px;")

        # Back Button
        back_btn = QPushButton("Back")
        back_btn.setFixedHeight(36)
        back_btn.clicked.connect(on_back_clicked)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.current_label)
        layout.addWidget(hint)
        layout.addStretch()
        layout.addWidget(back_btn)
        layout.addStretch()
        self.setLayout(layout)

        # Gesture states
        self._current_gesture = "REST"
        self._last_change_time: float | None = None
        self._timeout_s = 5.0 # 5 Seconds before returning to REST

        self.setFocusPolicy(Qt.StrongFocus)

        # Timer for REST timeout
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._check_timeout)
        self._timer.start()

    #---------------------------------------------------------
    # Key Handling 
    #---------------------------------------------------------

    def keyPressEvent(self, event):
        ch = event.text().lower()
        if ch == "r":
            self._set_gesture("ROCK")
        elif ch == "p":
            self._set_gesture("PAPER")
        elif ch == "s":
            self._set_gesture("SCISSORS")

    def _set_gesture(self, gesture: str):
        """
        Update the current gesture and reset the timer
        """
        self._current_gesture = gesture
        self._last_change_time = time.perf_counter()
        self.current_label.setText(f"Current Gesture: {gesture}")

    #------------------------------------------------------------------
    # Timer Logic: return "REST" after 5 seconds of inactivity 
    #------------------------------------------------------------------

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