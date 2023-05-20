'''
This stops the factory

Author: Lukas Beck
Date: 20.05.2023
'''
from revpimodio2 import RevPiModIO
import signal

from logger import log
class ExitHandler:
    def __init__(self, revpi: RevPiModIO) -> None:
        self.revpi = revpi

        signal.signal(signal.SIGINT, self.stop_factory)

    def stop_factory(self, signal=None, frame=None ):
        '''Disables the api for factory and stops all motors'''

        log.info("Program aborted: ")
        self.revpi.cleanup()

        try:
            exit_revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            exit_revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi\RevPi82247.img")
        
        log.info("Setting all outputs to false: ")

        list = exit_revpi.io

        not_used_words = ["PWM", "O_", "RevPiLED", "RS485ErrorLimit"]

        for io in list:
            if io.type == 301:
                is_out = True
                for word in not_used_words:
                    if str(io).find(word) != -1:
                        is_out = False
                
                if is_out:
                    exit_revpi.io[str(io)].value = False

        exit_revpi.exit()
    