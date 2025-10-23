import time
from app.io_adapters.keyboard_adapter import KeyboardAdapter
from app.modes.rps_mode import RPSMode

def main():
    print("Ultrasound Demo - RPS mode v0 \n"
          "Controls: r=ROCK, p=PAPER, s=SCISSORS. Ctrl+c to quit. \n"
          )
    
mode = RPSMode(countdown_ms=3000, window_ms=3000, k_samples=7)
kb = KeyboardAdapter

trial = 1
while trial < 5:
    print(f"\n=== Trial {trial} ===")
    result = mode.run_trial(kb.read)
    print(
        f"prediction : {result['prediction']:<9}  "
        f"confidence : {result['confidence']:.2f}  "
        f"latency : {result['latency_ms']:.1f} ms  "
        f"n_{result['n_samples']}, window={result['window_ms']} ms  "
    )
    
    trial += 1 
    time.sleep(1.0)

if __name__ == "__main__" :
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting Demo... Goodbye :(")
