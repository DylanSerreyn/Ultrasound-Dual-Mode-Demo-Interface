import time 
from collections import Counter

RPS_CLASSES = ("ROCK", "PAPER", "SCISSORS")
REST = "REST"

class RPSMode:
    '''

    '''

    def __init__(self, countdown_ms=0, window_ms=1000, k_samples=5):
        self.countdown_ms = countdown_ms
        self.window_ms = window_ms
        self.k_samples = k_samples 

    def run_trial(self, read_fn):
        '''

        '''

        start_time = time.perf_counter()
        deadline = start_time + (self.window_ms / 1000.0)
        samples = []

       

        #Capture window loop
        while time.perf_counter() < deadline and len(samples) < self.k_samples:
            token, t_event = read_fn()
            if token in RPS_CLASSES:
                samples.append((token, t_event))
            time.sleep(0.001)

        # Decide
        if not samples:
            # No input given; default to "rest"
            return {
                "prediction" : REST,
                "confidence" : 0.25,
                "latency_first_ms" : 0.0,
                "latency_last_ms"  : 0.0,
                "n_samples" : 0,
                "window_ms" : self.window_ms,
            }
        
        tokens = [t for (t, _) in samples]
        counts = Counter(tokens)
        pred, votes = counts.most_common(1)[0]
        total = len(tokens)
        confidence = votes/total

        first_time = samples[0][1]
        last_time = samples[-1][1]
        decision_time = time.perf_counter()

        latency_first_ms = (decision_time - first_time) * 1000.0
        latency_last_ms = (decision_time - last_time) * 1000.0

        return {
            "prediction" : pred,
            "confidence" : confidence,
            "latency_first_ms" : latency_first_ms,
            "latency_last_ms"  : latency_last_ms,
            "n_samples" : total,
            "window_ms" : self.window_ms,
        }
    
    def _countdown(self):
        seconds = max(self.countdown_ms // 1000, 0)

        for i in range(seconds, 0, -1):
            print(f"{i}...", flush=True)
            time.sleep(1.0)
        print("GO! (press r/p/s)", flush=True)