from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer

class TrackerPage(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)

        # Title
        title = QLabel("Continuous Tracker Mode")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; color: #555; margin-bottom: 6px;")

        # Status / countdown Label
        self.status = QLabel("Idle")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size: 14px; color: #555; margin-bottom: 8px;")
        
        # Buttons
        self.start_btn = QPushButton("Start Trial")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self._start_countdown)

        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedHeight(36)
        self.back_btn.clicked.connect(on_back_clicked)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.back_btn)
        btn_row.addStretch()


        # Layout
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.status)
        layout.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        self.setLayout(layout)

        # Countdown timer setup
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_remaining = 0 
        self._is_counting_down = False

        #------------------------------
        # Countdown Flow
        #------------------------------

    def _start_countdown(self):
        """ Begin a simple countdown (3..2..1..GO!)"""
        if self._is_counting_down:
            return
        self._is_counting_down = True
        self.start_btn.setEnabled(False)
        self.status.setText("Get Ready...")
        self._countdown_remaining = 3 
        self._update_countdown_label()
        self._countdown_timer.start()

    def _countdown_tick(self):
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._update_countdown_label()
            return
        
        self._countdown_timer.stop()
        self.status.setText("GO!")
        self._is_counting_down = False 

        self.start_btn.setEnabled(True)

    def _update_countdown_label(self):
        self.status.setText(f"{self._countdown_remaining}...")