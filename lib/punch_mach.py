'''This module controls the Punching Line with the connected Conveyor, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.15"

import threading
from enum import Enum

from lib.logger import log
from lib.machine import Machine
from lib.actuator import Actuator, SensorTimeoutError
from lib.conveyor import Conveyor

class State(Enum):
    START = 0
    CB_TO_PUNCH = 1
    PUNCHING = 2
    CB_TO_OUT = 3
    END = 100
    ERROR = 999

class PunchMach(Machine):
    '''Controls the Punching Maschine.'''
    '''
    Methodes:
        run(): Runs the Punching Maschine routine.
    Attributes:
        ready_for_transport (bool): If True then the next machine can transport the product.
    '''

    def __init__(self, revpi, name: str, line_name: str):
        '''Initializes the Punching Maschine.
        
        Args
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the machine in PiCtory (everything bevor first '_').
            line_name (str): Name of current line.
        '''
        super().__init__(revpi, name, line_name)
        self.position = 1
        self.ready_for_transport = False

        global log
        self.log = log.getChild(f"{self.line_name}(Pun)")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def run(self, out_stop_sensor: str, as_thread=True):
        '''Runs the Punching Maschine routine.
        
        Args:
            out_stop_sensor (str): Sensor at which the cb stops when outputting.
            as_thread (bool): Runs the function as a thread.
        '''
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(out_stop_sensor, False), name=self.name)
            self.thread.start()
            return
        
        self.switch_state(State.START)
        try:
            puncher = Actuator(self.revpi, self.name, self.line_name)
            cb_punch = Conveyor(self.revpi, "PM_CB", self.line_name)

            self.switch_state(State.CB_TO_PUNCH)
            # raise puncher
            puncher.run_to_sensor("UP", stop_sensor="PM_REF_SW_TOP", timeout_in_s=5, as_thread=True)
            # Move product from inner conveyor belt to puncher
            cb_punch.run_to_stop_sensor("FWD", stop_sensor="PM_SENS_PM", as_thread=False)

            puncher.join()
            self.switch_state(State.PUNCHING)
            self.log.info("Punching product")
            puncher.run_to_sensor("DOWN", stop_sensor="PM_REF_SW_BOTTOM", timeout_in_s=5)
            # raise puncher
            puncher.run_to_sensor("UP", stop_sensor="PM_REF_SW_TOP", timeout_in_s=5, as_thread=True)

            self.switch_state(State.CB_TO_OUT)

            #  Move product from puncher to connected conveyor
            cb_punch.run_to_stop_sensor("BWD", stop_sensor="PM_SENS_IN", as_thread=False)
            self.ready_for_transport = True
            #  Move product from puncher to connected conveyor
            cb_punch.run_to_stop_sensor("BWD", stop_sensor=out_stop_sensor, as_thread=False)

            puncher.join()
            del puncher
            del cb_punch

        except SensorTimeoutError as error:
            self.problem_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
        else:
            self.position += 1
            # self.end_machine = True # only if not called in the same functions as other cb
            self.switch_state(State.END)
