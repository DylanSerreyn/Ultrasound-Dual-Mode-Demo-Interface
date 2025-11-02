from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class TrackerPage(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)

        title = QLabel("Continuous Tracker Mode")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; color: #555; margin-bottom: 6px;")

        subtitle = QLabel("Keyboard prototype in progress...")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #555; margin-bottom: 6px;")

        back_btn = QPushButton("Back")
        back_btn.setFixedHeight(36)
        back_btn.clicked.connect(on_back_clicked)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(back_btn)
        layout.addStretch()
        self.setLayout(layout)