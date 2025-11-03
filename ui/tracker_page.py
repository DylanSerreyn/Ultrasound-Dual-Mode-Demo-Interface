from __future__ import annotations

import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer

from app.modes.tracker_mode import TrackerMode, TrackerConfig

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
        
        # Numeric readout (no plot yet)
        self.readout = QLabel("t = - s   target = -   user = -")
        self.readout.setAlignment(Qt.AlignCenter)
        self.readout.setStyleSheet("font-size: 14px; margin: 6px;")

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
        layout.addWidget(self.readout)
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

        # Trial tick timer
        self._tick_hz = 50.0 # 50 Hz by default
        self._tick_ms = int(1000.0 / self._tick_hz) # 20 ms
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(self._tick_ms)
        self._tick_timer.timeout.connect(self._tick)

        # Mode engine 
        cfg = TrackerConfig(
            duration_s=10.0,        # 10 Second trials
            tick_hz=self._tick_hz,  # for metrics' lag
            target_kind="sine",     # Generate sine wave
            target_freq_hz=0.3,     # ~3.3 s period
            target_amplitude=0.9,   
            stabilize_user=False,
            stabilize_alpha=0.15,
        )
        self.mode = TrackerMode(cfg)

        # Keyboard state with analog physics
        self.setFocusPolicy(Qt.StrongFocus)
        self._up_pressed = False
        self._down_pressed = False
        self.grabbed_keyboard = False

        # Physics params (needs tuning)
        self._user_value = 0.0        # Current slider value in [-1, 1]
        self._velocity = 0.0          # Internal velocity
        self._accel = 2.2             # units per second^2 when holding a key
        self._damping = 3.0           # velocity damping
        self._vmax = 3.0              # clamp velocity max
        self._last_tick_time = None   # perf_counter of last tick for dt

        #------------------------------
        # Countdown Flow
        #------------------------------

    def _start_countdown(self):
        """ Begin a simple countdown (3..2..1..GO!)"""
        if self._is_counting_down or self._tick_timer.isActive():
            return
        self._is_counting_down = True
        self.start_btn.setEnabled(False)

        # Reset engine and local state
        self._user_value = 0.0
        self._velocity = 0.0
        self._up_pressed = False
        self._down_pressed = False
        self._last_tick_time = None
        self.mode.start()

        # Countdown
        self.status.setText("Get Ready...")
        self._countdown_remaining = 3 
        self._update_countdown_label()
        self._countdown_timer.start()

    def _countdown_tick(self):
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._update_countdown_label()
            return
        
        # Show GO! and start trial next loop
        self._countdown_timer.stop()
        self.status.setText("GO!")
        self._is_counting_down = False 

        # Make sure we received keys during the trial
        self.setFocus()
        if not self.grabbed_keyboard:
            self.grabKeyboard()
            self.grabbed_keyboard = True

        # Start ticker
        self._last_tick_time = time.perf_counter()
        self._tick_timer.start()

    def _update_countdown_label(self):
        self.status.setText(f"{self._countdown_remaining}...")

    def _tick(self):
        """
        Advance the trial by one tick: update user via keyboard inputs, feed TrackerMode, update readout.
        """
        now = time.perf_counter()
        if self._last_tick_time is None:
            dt = 1.0 / self._tick_hz
        else:
            dt = max(0.0, now - self._last_tick_time)
        self._last_tick_time = now

        #---'Analog' Keyboard Physics---
        # input force: +1 for up, -1 for down, 0 for neither/both
        force = (1.0 if self._up_pressed else 0.0) - (1.0 if self._down_pressed else 0.0)

        # Accelerate velocity with damping
        self._velocity += self._accel * force * dt
        # clamp velocity to prevent runaway
        if self._velocity > self._vmax:
            self._velocity = self._vmax
        elif self._velocity < -self._vmax:
            self._velocity = -self._vmax
        
        # Damp it
        self._velocity -= self._damping * self._velocity * dt

        # Integrate into user value and clamp to [-1, 1]
        self._user_value += self._velocity * dt
        if self._user_value > 1.0:
            self._user_value = 1.0
            self._velocity = 0.0
        elif self._user_value < -1.0:
            self._user_value = -1.0
            self._velocity = 0.0

        # Step
        state = self.mode.step(t_now=now, user_val=self._user_value)

        # Update readout
        self.readout.setText(
            f"t = {state['t']:.2f} s  target = {state['target']:+.3f}  user = {state['user']:+.3f}"
        )

        # Stop
        if self.mode.finished():
            self._end_trial()
    
    def _end_trial(self):
        """
        Stop timers, release keyboard, compute metrics, show status.
        """
        self._tick_timer.stop()
        if self.grabbed_keyboard:
            self.releaseKeyboard()
            self.grabbed_keyboard = False

        self.mode.stop()
        metrics = self.mode.compute_metrics()
        self.status.setText(
            f"Trial Complete!  RMSE: {metrics['rmse']:.3f}   r: {metrics['r']:.3f}   "
            f"Lag: {metrics['lag_ms']:.0f} ms   RMSE at Best Lag: {metrics['rmse_best_lag']:.3f}"
        )
        self.start_btn.setEnabled(True)

    #---Key Handling---
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up:
            self._up_pressed = True
        elif key == Qt.Key_Down:
            self._down_pressed = True

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up:
            self._up_pressed = False
        elif key == Qt.Key_Down:
            self._down_pressed = False