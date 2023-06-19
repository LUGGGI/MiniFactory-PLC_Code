'''This module controls the Punching Line with the connected Conveyor, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading
from enum import Enum

from logger import log
from machine import Machine
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    CB_TO_PUNCH = 1
    PUNCHING = 2
    CB_TO_CB2 = 3
    CB_OUT = 4  
    END = 100
    ERROR = 999

class PunchMach(Machine):
    '''Controls the Punching Maschine.
    
    run(): Runs the Punching Maschine routine.
    '''

    def __init__(self, revpi, name: str):
        '''Initializes the Punching Maschine.
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.stage = 1
        log.debug("Created Punching Machine: " + self.name)

    def __del__(self):
        log.debug("Destroyed Punching Machine: " + self.name)

    def run(self, as_thread=False):
        '''Runs the Punching Maschine routine.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(), name=self.name)
            self.thread.start()
            return
        
        try:
            puncher = Actuator(self.revpi, self.name)
            cb_punch = Conveyor(self.revpi, "PM_CB")

            self.state = self.switch_state(State.CB_TO_PUNCH)
            # raise puncher
            puncher.run_to_sensor("UP", stop_sensor="PM_REF_SW_TOP", as_thread=True)
            # Move product from inner conveyor belt to puncher
            cb_punch.run_to_stop_sensor("FWD", stop_sensor="PM_SENS_PM", start_sensor="CB2_SENS_END", as_thread=False)

            puncher.join()
            self.state = self.switch_state(State.PUNCHING)
            log.info("Punching product")
            puncher.run_to_sensor("DOWN", stop_sensor="PM_REF_SW_BOTTOM")
            # raise puncher
            puncher.run_to_sensor("UP", stop_sensor="PM_REF_SW_TOP", as_thread=True)

            self.state = self.switch_state(State.CB_TO_CB2)
            self.ready_for_transport = True
            #  Move product from puncher to connected conveyor
            cb_punch.run_to_stop_sensor("BWD", stop_sensor="CB2_SENS_END", as_thread=False)

            puncher.join()
            del puncher
            del cb_punch

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.stage += 1
