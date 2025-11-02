from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt 

class LandingPage(QWidget):
    def __init__(self, on_rps_clicked, on_tracker_clicked, parent=None):
        super().__init__(parent)

        title = QLabel("Ultrasound Demo Interface")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 700; margin: 12px;")

        rps_btn = QPushButton("Rock-Paper-Scissors (Discrete)")
        rps_btn.setFixedHeight(48)
        rps_btn.clicked.connect(on_rps_clicked)

        tracker_btn = QPushButton("Continuous Tracker (Regression)")
        tracker_btn.setFixedHeight(48)
        tracker_btn.clicked.connect(on_tracker_clicked)


        self.dont_click_btn = QPushButton("Exit")
        self.dont_click_btn.setFixedHeight(40)
        self.dont_click_btn.clicked.connect(self._dont_click_handler)
        self._dont_click_stage = 0
        
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addSpacing(12)
        layout.addWidget(rps_btn)
        layout.addWidget(tracker_btn)
        layout.addWidget(self.dont_click_btn) # haha
        layout.addStretch()
        self.setLayout(layout)

    def _dont_click_handler(self):
            from PySide6.QtWidgets import QApplication
            QApplication.quit()