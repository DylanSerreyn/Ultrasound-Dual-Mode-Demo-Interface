import time
import random
from app.io_adapters.keyboard_adapter import KeyboardAdapter
from app.modes.rps_mode import RPSMode

RPS = ("ROCK", "PAPER", "SCISSORS")


def pick_opponent():
    return random.choice(RPS)

def outcome(user: str, opp: str) -> str:
    '''
    
    '''
    
    if user not in RPS:
        return "LOSE"
    if user == opp:
        return "TIE"
    
    wins_over = {
        "ROCK" : "SCISSORS",
        "PAPER" : "ROCK",
        "SCISSORS" : "PAPER",
    }
    if wins_over[user] == opp:
        return "WIN"
    else:
        return "LOSE"



def main():
    print("Ultrasound Demo - RPS mode v0 \n"
          "Controls: r=ROCK, p=PAPER, s=SCISSORS. Ctrl+c to quit. \n"
          )
    
mode = RPSMode(countdown_ms=3000, window_ms=3000, k_samples=7)
kb = KeyboardAdapter

win_count = 0
lose_count = 0
tie_count = 0

trial = 1
while True:
    print(f"\n=== Trial {trial} ===")
    opp = pick_opponent()

    result = mode.run_trial(kb.read)
    user_choice = result["prediction"]

    result_outcome = outcome(user_choice, opp)

    if result_outcome == "WIN":
            win_count += 1
    elif result_outcome == "LOSE":
            lose_count += 1
    elif result_outcome == "TIE":
            tie_count += 1

    print(
        f"Opponent: {opp:<9} "
        f"Your Choice: {user_choice:<9} "
        f"Outcome: {result_outcome}"
    )
    print(
        f"confidence : {result['confidence']:.2f}  "
        f"latency : {result['latency_ms']:.1f} ms  "
        f"n_{result['n_samples']}, window={result['window_ms']} ms  "
    )
    
    ans = input("Ready for the next trial? (y/n): ").strip().lower()
    if ans != "y":
        print("\n=== Final Results ===")
        print(f"Total Wins:   {win_count}")
        print(f"Total Losses: {lose_count}")
        print(f"Total Ties:   {tie_count}")
        break

    trial += 1 
    time.sleep(0.2)

if __name__ == "__main__" :
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting Demo... Goodbye :(")
