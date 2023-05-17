import time
import atexit
import threading
from logger import log




def exit_fkt():
    log.info("exit")
def test():
    while(True):
        log.info("fkt")
        time.sleep(1)

atexit.register(exit_fkt)
threading.Thread(target=test).start()

while(True):
    log.info("main")
    time.sleep(1)