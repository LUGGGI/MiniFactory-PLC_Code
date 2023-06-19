'''This module controls the Sorting Line, it inherits from machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading
from time import sleep
from enum import Enum

from logger import log
from sensor import Sensor
from machine import Machine
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    COLOR_SENSING = 1
    SORTING = 2   
    END = 100
    ERROR = 999

class SortLine(Machine):
    '''Controls the Sorting Line

    run(): Runs the Sorting Line routine.
    '''
    color = "WHITE"

    def __init__(self, revpi, name: str):
        '''Initializes the Sorting Line
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.stage = 1
        log.debug("Created Sorting Line: " + self.name)


    def __del__(self):
        log.debug("Destroyed Sorting Line: " + self.name)


    def run(self, as_thread=True):
        '''Runs the Sorting Line routine.
        
        :as_thread: Runs the function as a thread
        '''      
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            # Color Sensing
            self.state = self.switch_state(State.COLOR_SENSING)
            cb = Conveyor(self.revpi, f"{self.name}_CB_FWD")

            # TODO: Handle color sensing
            # color_sensor = Sensor(self.revpi, f"{self.name}_COLOR_SENSOR")

            # move product through color sensor
            cb.run_to_stop_sensor("", f"{self.name}_CB_SENS_PISTON", as_thread=False)

            log.info(f"{self.name} :Color detected: {self.color}")

            # SORTING
            self.state = self.switch_state(State.SORTING)
            compressor = Actuator(self.revpi, f"{self.name}_COMPRESSOR")

            self.start_next_machine = True
            # determine sorting position
            position = 0
            if self.color == "WHITE":
                position = 2
            elif self.color == "RED":
                position = 11
            elif self.color == "BLUE":
                position = 19

            # run to desired bay
            cb.run_to_counter_value("", f"{self.name}_CB_COUNTER", position, as_thread=False)
            del cb
            # push into bay
            compressor.start()
            sleep(0.2)
            Actuator(self.revpi, f"{self.name}_VALVE_PISTON_{self.color}").run_for_time("", 0.5)
            compressor.stop()
            # check if in bay
            sleep(1)
            if Sensor(self.revpi, f"{self.name}_SENS_{self.color}").get_current_value() == False:
                # no detection at sensor
                raise(Exception(f"{self.name} :Product not in right bay"))

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.info(f"{self.name} :Product sorted into: {self.color}")
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
            self.stage += 1