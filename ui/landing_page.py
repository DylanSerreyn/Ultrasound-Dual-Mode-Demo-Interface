from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt 

class LandingPage(QWidget):
    def __init__(self, on_rps_clicked, on_tracker_clicked, on_test_clicked, parent=None):
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

        test_btn = QPushButton("Test Mode")
        test_btn.setFixedHeight(48)
        test_btn.clicked.connect(on_test_clicked)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setFixedHeight(40)
        self.exit_btn.clicked.connect(self._exit_click_handler)

        for btn in (rps_btn, tracker_btn, test_btn):
             btn.setMinimumHeight(44)
             btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        
        main_layout = QVBoxLayout(self)
        #main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        main_layout.addWidget(title)

        # Mode buttons (Center Column)
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setSpacing(6)

        
        center_layout.addSpacing(8)
        center_layout.addWidget(rps_btn)
        center_layout.addWidget(tracker_btn)
        center_layout.addWidget(test_btn)

        main_layout.addWidget(center_widget, alignment=Qt.AlignHCenter)

        main_layout.addStretch()
        main_layout.addWidget(self.exit_btn, alignment=Qt.AlignRight)

        self.setLayout(main_layout)


    def _exit_click_handler(self):
            from PySide6.QtWidgets import QApplication
            QApplication.quit()