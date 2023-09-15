'''This module controls the Indexed Line with two Machining Stations (Mill and Drill), it inherits from machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.15"

import threading
from time import sleep
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor, SensorTimeoutError
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    START = 0
    TO_MILL = 1
    MILLING = 2        
    TO_DRILL = 3
    DRILLING = 4
    TO_OUT = 5      
    END = 100
    ERROR = 999

class IndexLine(Machine):
    '''Controls the Index Line.

    Methodes:
        run(): Runs the Index Line routine.
    Attributes:
        __TIME_MILLING (int): Time that the mill should be active.
        __TIME_DRILLING (int): Time that the drill should be active.
        start_next_machine(bool): Is set to True if next machine should be started.
    '''
    __TIME_MILLING = 1
    __TIME_DRILLING = 1

    def __init__(self, revpi, name: str, line_name: str):
        '''Initializes the Index Line.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the sensor in PiCtory (everything bevor first '_').
            line_name (str): Name of current line.
        '''
        super().__init__(revpi, name, line_name)
        
        self.start_next_machine = False
        global log
        self.log = log.getChild(f"{self.line_name}(Indx)")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def run(self, as_thread=True):
        '''Runs the Index Line routine.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''      
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(False,), name=self.name)
            self.thread.start()
            return

        self.switch_state(State.START)
        try:
            cb_mill = Conveyor(self.revpi, self.name + "_CB_MIll", self.line_name)

            # Move product to Mill
            self.switch_state(State.TO_MILL)
            pusher_in = Actuator(self.revpi, self.name + "_PUSH1", self.line_name)
            cb_start = Conveyor(self.revpi, self.name + "_CB_START", self.line_name)

            # move pusher to back
            pusher_in.run_to_sensor("BWD", self.name + "_REF_SW_PUSH1_BACK", timeout_in_s=5, as_thread=True) 
            # move product to pusher_in
            cb_start.run_to_stop_sensor("", self.name + "_REF_SW_PUSH1_FRONT", as_thread=True)
            # wait for product to be detected by sensor 
            Sensor(self.revpi, self.name + "_SENS_PUSH1", self.line_name).wait_for_detect()
            sleep(1) # wait for product to be in front of pusher
            # push product to cb_mill
            pusher_in.join()
            cb_start.join()
            del cb_start
            pusher_in.run_to_sensor("FWD", self.name + "_REF_SW_PUSH1_FRONT", timeout_in_s=5, as_thread=True) 
            cb_mill.run_to_stop_sensor("", self.name + "_SENS_MILL", as_thread=False)
            # move pusher back to back
            pusher_in.join()
            pusher_in.run_to_sensor("BWD", self.name + "_REF_SW_PUSH1_BACK", timeout_in_s=5, as_thread=True)
            

            # Milling
            self.switch_state(State.MILLING)
            Actuator(self.revpi, self.name + "_MILL_MOTOR", self.line_name).run_for_time("", self.__TIME_MILLING)


            cb_drill = Conveyor(self.revpi, self.name + "_CB_DRIll", self.line_name)

            # Move product to Drill
            self.switch_state(State.TO_DRILL)
            cb_mill.run_to_stop_sensor("", self.name + "_SENS_DRILL", as_thread=True)
            cb_drill.run_to_stop_sensor("", self.name + "_SENS_DRILL", as_thread=False)

            cb_mill.join()
            pusher_in.join()
            del pusher_in
            del cb_mill


            self.start_next_machine = True
            # Drilling
            self.switch_state(State.DRILLING)
            Actuator(self.revpi, self.name + "_DRILL_MOTOR", self.line_name).run_for_time("", self.__TIME_DRILLING)


            # Move product to Out
            self.switch_state(State.TO_OUT)
            pusher_out = Actuator(self.revpi, self.name + "_PUSH2", self.line_name)
            cb_end = Conveyor(self.revpi, self.name + "_CB_END", self.line_name)

            # move pusher to back
            pusher_out.run_to_sensor("BWD", self.name + "_REF_SW_PUSH2_BACK", timeout_in_s=5, as_thread=True)
            # move product to pusher_out
            cb_drill.run_to_stop_sensor("", self.name + "_REF_SW_PUSH2_FRONT", as_thread=True)
            sleep(1) # wait for product to be in front of pusher
            # push product to out
            pusher_out.join()
            pusher_out.run_to_sensor("FWD", self.name + "_REF_SW_PUSH2_FRONT", timeout_in_s=5, as_thread=True) 
            cb_end.run_to_stop_sensor("", self.name + "_SENS_END", stop_delay_in_ms=1000, as_thread=False)
            del cb_end
            # move pusher back to back
            pusher_out.run_to_sensor("BWD", self.name + "_REF_SW_PUSH2_BACK", timeout_in_s=5, as_thread=True) 

            cb_drill.join()
            pusher_out.join()
            del cb_drill
            del pusher_out
        except SensorTimeoutError as error:
            self.problem_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)

        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
        else:  
            self.end_machine = True
            self.position += 1
            self.switch_state(State.END)
