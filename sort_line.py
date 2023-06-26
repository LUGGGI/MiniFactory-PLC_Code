'''This module controls the Sorting Line, it inherits from machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.22"

import threading
from time import sleep
from enum import Enum

from logger import log
from sensor import Sensor
from machine import Machine
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    START = 0
    COLOR_SENSING = 1
    SORTING = 2
    INTO_BAY = 3
    END = 100
    ERROR = 999

class SortLine(Machine):
    '''Controls the Sorting Line

    run(): Runs the Sorting Line routine.
    '''

    def __init__(self, revpi, name: str):
        '''Initializes the Sorting Line
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.stage = 1
        self.color = "WHITE"
        log.debug("Created Sorting Line: " + self.name)


    def __del__(self):
        log.debug("Destroyed Sorting Line: " + self.name)


    def run(self, color: str=None, as_thread=True):
        '''Runs the Sorting Line routine.
        
        :as_thread: Runs the function as a thread
        '''      
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(color, False), name=self.name)
            self.thread.start()
            return

        self.state = self.switch_state(State.START)
        try:
            # Color Sensing
            self.state = self.switch_state(State.COLOR_SENSING)
            cb = Conveyor(self.revpi, f"{self.name}_CB_FWD")

            # TODO: Handle color sensing
            # color_sensor = Sensor(self.revpi, f"{self.name}_COLOR_SENSOR")

            # move product through color sensor
            cb.run_to_stop_sensor("", stop_sensor=f"{self.name}_CB_SENS_PISTON", as_thread=False)

            if color:
                self.color = color
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
                position = 7
            elif self.color == "BLUE":
                position = 12

            self.start_next_machine = True
            # run to desired bay
            cb.run_to_counter_value("", f"{self.name}_CB_COUNTER", position, as_thread=False)
            del cb

            self.state = self.switch_state(State.INTO_BAY)
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
            log.warning(f"{self.name} :Product sorted into: {self.color}")
            self.ready_for_transport = True
            self.state = self.switch_state(State.END)
            self.end_machine = True
            self.stage += 1