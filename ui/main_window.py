from PySide6.QtWidgets import QMainWindow, QWidget, QStackedWidget
from app.ui.landing_page import LandingPage
from app.ui.rps_page import RPSPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultrasound Demo Interface")
        self.resize(900,520)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pages
        self.landing = LandingPage(
            on_rps_clicked=self._go_rps,
            on_tracker_clicked=self._go_tracker_stub
        )
        self.rps = RPSPage(on_back_clicked=self._go_landing)

        self.stack.addWidget(self.landing) # index 0
        self.stack.addWidget(self.rps)     # index 1

        self.stack.setCurrentIndex(0)

    def _go_landing(self):
        self.stack.setCurrentIndex(0)

    def _go_rps(self):
        self.stack.setCurrentIndex(1)

    def _go_tracker_stub(self):
        # Don't have that yet
        pass