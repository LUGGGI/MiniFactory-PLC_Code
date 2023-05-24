'''This handles exit/stop of factory'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

from revpimodio2 import RevPiModIO
import signal

from logger import log

class ExitHandler:
    '''Stops the factory, and handles CTRL+C
    
    stop_factory: Disables the API for factory and stops all Actuators
    '''
    was_called = False
    def __init__(self, revpi: RevPiModIO) -> None:
        '''Initializes the ExitHandler
        
        :revpi: RevPiModIO Object to control the motors and sensors
        '''
        self.revpi = revpi

        signal.signal(signal.SIGINT, self.stop_factory)


    def stop_factory(self, *_):
        '''Disables the API for factory and stops all Actuators'''
        self.was_called = True
        log.info("Program aborted: ")
        self.revpi.cleanup() # stop API access for factory

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
    