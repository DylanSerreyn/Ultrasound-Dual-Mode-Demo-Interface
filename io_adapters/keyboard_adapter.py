import time
import msvcrt #Standard windows io library 

TOKENS = {
    b"r" : "ROCK",
    b"p" : "PAPER",
    b"s" : "SCISSORS",
}

class KeyboardAdapter:
    '''
        Windows terminal key adapter using msvcrt.
        read() returns pressed token and timestamp if r,p,s is pressed.
        if no token is pressed return (none, none)
     
    '''
    
    def read(self):
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            ch = ch.lower()
            t = time.perf_counter()

            return TOKENS.get(ch), t
        return None, None 
    