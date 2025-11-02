import random 
import time
import queue

from PySide6.QtCore import QObject, Signal, QThread, QTimer, Qt 
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)

from app.modes.rps_mode import RPSMode

RPS = ("ROCK", "PAPER", "SCISSORS")

def pick_opponent():
    return random.choice(RPS)

def outcome(user: str, opp: str) -> str:
    if user not in RPS:
        return "LOSE"
    if user == opp:
        return "TIE"
    wins_over = {
        "ROCK" : "SCISSORS",
        "SCISSORS" : "PAPER",
        "PAPER" : "ROCK",
    }
    return "WIN" if wins_over[user] == opp else "LOSE"

class KeyBuffer:
    """ Non-Blocking key buffer for r/p/s tokens."""
    def __init__(self):
        self._q = queue.Queue()

    def push(self, token: str):
        self._q.put((token, time.perf_counter()))

    def read(self):
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return (None, None)
        
    def clear(self):
        with self._q.mutex:
            self._q.queue.clear()

#--------------------------------Worker To Run Single Trial-----------------------------
class TrialWorker(QObject):
    finished = Signal(dict, str) # Emits (result_dict, opponent_choice)

    def __init__(self, mode: RPSMode, read_fn):
        super().__init__()
        self.mode = mode
        self.read_fn = read_fn

    def run(self):
        opp = pick_opponent()
        result = self.mode.run_trial(self.read_fn)
        self.finished.emit(result, opp)

#----------------------------------RPS Page UI-------------------------------------------
class RPSPage(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)

        self.mode = RPSMode(countdown_ms=0, window_ms=2000, k_samples=5)
        
        # Input buffer for GUI-Captured keys
        self.key_buffer = KeyBuffer()
        self.setFocusPolicy(Qt.StrongFocus)

        # Scoreboard:
        self.win_count = 0
        self.lose_count = 0
        self.tie_count = 0

        # Running sums for summary report 
        self._trial_count = 0
        self._sum_conf = 0.0
        self._sum_lat_last = 0.0
        self._sum_lat_first = 0.0
        self._sum_n = 0

        # Title
        title = QLabel("Rock-Paper-Scissors")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 700; margin: 8px;")

        # Status Line
        self.status = QLabel("Idle")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size: 14px; color: #555;")

        # 3 Boxes
        self.your_pred_box = self._make_big_box("Your Prediction", "-")
        self.outcome_box   = self._make_big_box("Outcome (W/L/T)", "-")
        self.opp_box       = self._make_big_box("Opponent's Choice", "-")

        # Summary label
        self.summary_label = QLabel("Summary: -")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setStyleSheet("font-size: 13px; margin: 6px; color: #333;")

        boxes = QHBoxLayout()
        boxes.addWidget(self.your_pred_box)
        boxes.addWidget(self.outcome_box)
        boxes.addWidget(self.opp_box)

        # Metrics Line
        self.metrics = QLabel("Confidence: -  Latency(last): - ms  Latency(first): - ms  (n=-, window=- ms)")
        self.metrics.setAlignment(Qt.AlignCenter)
        self.metrics.setStyleSheet("font-size: 13px; margin: 6px;")

        # Buttons
        self.start_btn = QPushButton("Start Trial")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self._start_trial)

        self.next_btn = QPushButton("Next Trial")
        self.next_btn.setFixedHeight(40)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._start_trial)

        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedHeight(36)
        self.back_btn.clicked.connect(on_back_clicked)

        self.summary_btn = QPushButton("Generate Summary Report")
        self.summary_btn.setFixedHeight(36)
        self.summary_btn.clicked.connect(self._generate_summary)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.next_btn)
        btn_row.addWidget(self.summary_btn)
        btn_row.addWidget(self.back_btn)
        btn_row.addStretch()

        # Page Layout
        root = QVBoxLayout()
        root.addWidget(title)
        root.addWidget(self.status)
        root.addSpacing(8)
        root.addLayout(boxes)
        root.addSpacing(8)
        root.addWidget(self.summary_label)
        root.addWidget(self.metrics)
        root.addSpacing(8)
        root.addLayout(btn_row)
        root.addStretch()
        self.setLayout(root)

        # Thread Placeholders
        self._thread: QThread | None = None
        self._worker: TrialWorker | None = None

        # Countdown
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_remaining = 0

        #----------------------------Helpers-----------------------------
    def _make_big_box(self, heading: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("QFrame { border: 1px solid #aaa; border-radius: 8px; }")
        v = QVBoxLayout(frame)

        hlabel = QLabel(heading)
        hlabel.setAlignment(Qt.AlignCenter)
        hlabel.setStyleSheet("font-size: 16px; font-weight: 600; margin-top: 6px;")

        vlabel = QLabel(value)
        vlabel.setAlignment(Qt.AlignCenter)
        vlabel.setStyleSheet("font-size: 22px; margin: 12px;")

        # Show Outcome, Including running totals 
        if "Outcome" in heading:
            self.score_label = QLabel("Wins: 0  Losses: 0  Ties: 0")
            self.score_label.setAlignment(Qt.AlignCenter)
            self.score_label.setStyleSheet("font-size: 12px; color: #555; margin-bottom: 6px;")
            v.addWidget(hlabel)
            v.addWidget(vlabel)
            v.addWidget(self.score_label)
        else:
            v.addWidget(hlabel)
            v.addWidget(vlabel)

        frame._value_label = vlabel # Store for updates
        return frame 
    
    def _set_box_value(self, box: QFrame, text: str):
        box._value_label.setText(text)

    #-------------------------Trial Control----------------------------
    def keyPressEvent(self, event):
        ch = event.text().lower()
        if ch in ("r", "p", "s"):
            mapping = {"r" : "ROCK", "p" : "PAPER", "s" : "SCISSORS"}
            self.key_buffer.push(mapping[ch])
    
    def _start_trial(self):
        # UI State
        self.start_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self._set_box_value(self.your_pred_box, "-")
        self._set_box_value(self.outcome_box, "-")
        self._set_box_value(self.opp_box, "-")
        self.metrics.setText("Confidence: -  Latency(last): - ms  Latency(first): - ms  (n=-, window=- ms )")
        self.status.setText("Get ready...")
        self.setFocus()
        self.grabKeyboard()
        self.key_buffer.clear()

        # Start Worker thread to run a blocking trial
        self._countdown_remaining = 3
        self._update_countdown_label()
        self._countdown_timer.start()

    def _countdown_tick(self):
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._update_countdown_label()
            return
        
        self.status.setText("Go! (Press R / P / S)")
        self._countdown_timer.stop()

        QTimer.singleShot(0, self._launch_worker)

    def _update_countdown_label(self):
        self.status.setText(f"{self._countdown_remaining}...")

    def _launch_worker(self):
        # Launch trial worker
        self._thread = QThread()
        self._worker = TrialWorker(self.mode, self.key_buffer.read)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._trial_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _trial_finished(self, result: dict, opponent: str):
        # Update UI With Results
        self.releaseKeyboard()
        user_choice = result["prediction"]
        self._set_box_value(self.your_pred_box, user_choice)
        self._set_box_value(self.opp_box, opponent)

        # Outcome + Scoreboard
        out = outcome(user_choice, opponent)
        if out == "WIN":
            self.win_count += 1
        elif out == "LOSE":
            self.lose_count += 1 
        else:
            self.tie_count += 1

        lat_last = result.get("latency_last_ms", result.get("latency_ms", 0.0))
        lat_first = result.get("latency_first_ms", 0.0)
        self._trial_count += 1
        self._sum_conf += result.get("confidence", 0.0)
        self._sum_lat_last += lat_last
        self._sum_lat_first += lat_first
        self._sum_n += result.get("n_samples", 0)

        self._set_box_value(self.outcome_box, out)
        self.score_label.setText(
            f"Wins: {self.win_count}  Losses: {self.lose_count}  Ties: {self.tie_count}"
        )

        # Metrics
        lat_last = result.get("latency_last_ms", result.get("latency_ms", 0.0))
        lat_first = result.get("latency_first_ms", 0.0)

        self.metrics.setText(
            f"Confidence: {result['confidence']:.2f}  "
            f"Latency(last): {lat_last:.1f} ms  "
            f"Latency(first): {lat_first:.1f} ms  "
            f"(n={result['n_samples']}, window = {result['window_ms']} ms)"
        )

        self.status.setText("Trial Complete.")
        self.start_btn.setEnabled(True)
        self.next_btn.setEnabled(True)

    def _generate_summary(self):
        """
        Compute and display a summary report across all completed trials
        """
                    
        if self._trial_count == 0:
            self.summary_label.setText("Summary Not Available, No Trials Yet.")
            return 
        
        avg_conf = self._sum_conf / self._trial_count
        avg_lat_last = self._sum_lat_last / self._trial_count
        avg_lat_first = self._sum_lat_first / self._trial_count
        avg_n = self._sum_n / self._trial_count

        self.summary_label.setText(
            f"| Number of Trials: {self._trial_count}  | "
            f"Average Confidence: {avg_conf:.2f}  | "
            f"Average N_Samples: {avg_n:.1f} |"
            f"\nAverage Latency (last input to decision): {avg_lat_last:.1f} ms  "
            f"\nAverage Latency (first input to decision): {avg_lat_first:.1f} ms  "   
        )


        