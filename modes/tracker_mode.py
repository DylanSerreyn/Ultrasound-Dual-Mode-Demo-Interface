"""

"""

from __future__ import annotations 
import math
import time
from dataclasses import dataclass
from typing import Literal, Optional, Dict, List
import numpy as np

TargetKind = Literal["sine", "steps"]

def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """
    """
    return lo if x < lo else hi if x > hi else x

@dataclass
class TrackerConfig:
    """
    Tunable configuration for a single trial
    """

    duration_s: float = 15.0 
    tick_hz: float = 50.0
    target_kind: TargetKind = "sine"
    target_freq_hz: float = 0.3
    target_amplitude: float = 0.9
    target_phase: float = 0.0
    stabilize_user: bool = False 
    stabilize_alpha: float = 0.15

class TrackerMode:
    """
    
    """

    def __init__(self, config: Optional[TrackerConfig] = None):
        self.cfg = config or TrackerConfig()

        # Timing
        self._t0: Optional[float] = None
        self._t_last: Optional[float] = None
        self._running: bool = False

        # Buffers
        self.times: List[float] = []
        self.target_vals: List[float] = []
        self.user_vals: List[float] = []

        # Internal state for user stabilization
        self._user_smoothed: Optional[float] = None

        #---------------------------------------
        # Trial Lifecycle 
        #---------------------------------------

    def start(self) -> None:
        """
        """
        self.reset_buffers()
        self._t0 = time.perf_counter()
        self._t_last = None
        self._running = True 
        self._user_smoothed = None

    def stop(self) -> None:
        """"""
        self._running = False

    def reset_buffers(self) -> None:
        """"""
        self.times.clear()
        self.target_vals.clear()
        self.user_vals.clear()

    def finished(self) -> bool:
        """"""
        if not self._running or self._t0 is None:
            return False
        if not self.times:
            return False 
        return self.times[-1] >= self.cfg.duration_s
    
    #------------------------------------------------
    # Main ticking API
    #------------------------------------------------
    def step(self, t_now: float, user_val: float) -> Dict[str, float]:
        """"""
        if not self._running or self._t0 is None:
            # Return 0s if step is called while not running 
            return {"t": 0.0, "target": 0.0, "user": 0.0}
        
        t = max(0.0, t_now - self._t0)            # Elapsed time this trial

        target = self._target_value(t)            # Target value at elapsed time

        user = _clamp(float(user_val), -1.0, 1.0) # Safety-clamp user input

        # Optional stabilization
        if self.cfg.stabilize_user:
            if self._user_smoothed is None:
                self._user_smoothed = user
            else:
                a = float(self.cfg.stabilize_alpha)
                # Stabilizer: y[t] = (1 - a)*y[t-1] + a*u[t]
                self._user_smoothed = (1.0 - a) * self.user_smoothed + a * user
            user_out = _clamp(self._user_smoothed, -1.0, 1.0)
        else:
            user_out = user

        # Append to buffers 
        self.times.append(t)
        self.target_vals.append(target)
        self.user_vals.append(user_out)

        # Stop when trial duration is reached
        if t >= self.cfg.duration_s:
            self._running = False

        self._t_last = t_now

        return {"t": t, "target": target, "user": user_out}
    
    #------------------------------------------------------------
    # Target generator
    #------------------------------------------------------------

    def _target_value(self, t: float) -> float:
        """
        """
        kind = self.cfg.target_kind
        if kind == "sine":
            return self._target_sine(t)
        elif kind == "steps":
            return self._target_steps(t)
        else:
            return self._target_sine(t)
        
    def _target_sine(self, t: float) -> float:
        """
        Generates a target sine wave with the cfg parameters
        """
        A = float(self.cfg.target_amplitude)
        f = float(self.cfg.target_freq_hz)
        phi = float(self.cfg.target_phase)
        val = A * math.sin(2.0 * math.pi * f * t + phi)

        return _clamp(val, -1.0, 1.0)
    
    def _target_steps(self, t: float) -> float:
        """
        Step target cycles through fixed levels every 'segment_s' 
        """
        A = float(self.cfg.target_amplitude)
        f = float(self.cfg.target_freq_hz)
        
        # 
        segment_s = 0.5 / f

        # define levels for the "staircase"
        levels = (-A, -0.5 * 5, 0.0, 0.5 * A, A, 0.5 * A, 0.0, -0.5 * A)
        idx = int(t // segment_s) % len(levels)

        return _clamp(levels[idx], -1.0, 1.0)
    
    #--------------------------------------------
    # Metrics
    #--------------------------------------------
    def compute_metrics(self) -> Dict[str, float]:
        """
        
        """

        if len(self.times) < 3:
            return {
                "rmse": 0.0,
                "r": 0.0,
                "lag_ms": 0.0,
                "rmse_best_lag": 0.0,
                "n": float(len(self.times)),
                "duration_s": float(self.times[-1] if self.times else 0.0),
            }

        t = np.asarray(self.times, dtype=np.float64)
        y = np.asarray(self.user_vals, dtype=np.float64)
        x = np.asarray(self.target_vals, dtype=np.float64)

        # Basic RMSE
        rmse = float(np.sqrt(np.mean((y - x) ** 2)))

        # Pearson r to guard against constant vectors 
        if np.std(x) < 1e-12 or np.std(y) < 1e-12:
            r = 0.0
        else:
            r = float(np.corrcoef(x, y)[0, 1])

        # Estimate an average sample period
        dt = float(np.mean(np.diff(t))) if len(t) >= 2 else (1.0 / max(self.cfg.tick_hz, 1e-6))

        # Estimate lag
        x0 = x - np.mean(x)
        y0 = y - np.mean(y)
        corr = np.correlate(y0, x0, mode="full") # Correlate user vs target
        lags = np.arrange(-len(x) + 1, len(x), dtype=np.float64)
        k_best = int(lags[np.argmax(corr)])
        lag_ms = float(k_best * dt * 1000.0)

        # Compute RMSE at best lag
        rmse_best = float(self._rmse_with_lag(x, y, k_best))

        return {
            "rmse": rmse,
            "r": r,
            "lag_ms": lag_ms,
            "rmse_best_lag": rmse_best,
            "n": float(len(t)),
            "duration_s": float(t[-1]),
        }
    
    @staticmethod
    def _rmse_with_lag(x: np.ndarray, y: np.ndarray, k: int) -> float:
        """
        RMSE after shifting 'y' by k samples relative to 'x'
        """
        if k == 0:
            seg_x, seg_y = x, y
        elif k > 0:
            # y lags: drop the first k of y and last k of x
            seg_x = x[:-k] if k < len(x) else x[:0]
            seg_y = y[k:] if k < len(y) else y[:0]
        else:
            # x lags: drop first -k of x and last -k of y
            kk = -k
            seg_x = x[kk:] if kk < len(x) else x[:0]
            seg_y = y[:-kk] if kk < len(y) else y[:0]
        
        if len(seg_x) == 0 or len(seg_y) == 0:
            return 0.0
        return float(np.sqrt(np.mean((seg_y - seg_x) ** 2)))