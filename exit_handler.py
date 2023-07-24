'''This handles exit/stop of factory'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.24"

import threading
from time import sleep
from revpimodio2 import RevPiModIO
import signal

from logger import log

class ExitHandler:
    '''Stops the factory, and handles CTRL+C
    
    stop_factory: Disables the API for factory and stops all Actuators
    '''
    def __init__(self, revpi: RevPiModIO) -> None:
        '''Initializes the ExitHandler
        
        :revpi: RevPiModIO Object to control the motors and sensors
        '''
        self.revpi = revpi
        self.was_called = False

        signal.signal(signal.SIGINT, self.stop_factory)


    def stop_factory(self, *_):
        '''Disables the API for factory and stops all Actuators'''
        # call this function again as a thread
        if self.was_called == False:
            self.was_called = True
            self.thread = threading.Thread(target=self.stop_factory, name="STOP")
            self.thread.start()
            return
        
        log.critical("Program aborted: ")
        self.revpi.cleanup() # stop API access for factory

        try:
            exit_revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            exit_revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.img")

        log.critical("Setting all outputs to false: ")

        list = exit_revpi.io

        not_used_words = ["PWM_", "RevPiLED", "RS485ErrorLimit"]

        for io in list:
            if io.type == 301:
                is_out = True
                for word in not_used_words:
                    if str(io).find(word) != -1:
                        is_out = False

                if is_out:
                    exit_revpi.io[str(io)].value = 0

        sleep(0.5)
        for io in list:
            if io.type == 301:
                is_out = True
                for word in not_used_words:
                    if str(io).find(word) != -1:
                        is_out = False

                if is_out:
                    exit_revpi.io[str(io)].value = 0

        exit_revpi.exit()


# Start stop factory if called as script
if __name__ == "__main__":
    ExitHandler.stop_factory(ExitHandler(RevPiModIO()))