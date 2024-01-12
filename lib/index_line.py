'''This module controls the Indexed Line with two Machining Stations (Mill and Drill), it inherits from machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.12"

import threading
from enum import Enum

from lib.logger import log
from lib.machine import Machine, MainState
from lib.sensor import Sensor, SensorTimeoutError
from lib.actuator import Actuator
from lib.conveyor import Conveyor

class State(Enum):
    START = 0
    TO_MILL = 1
    MILLING = 2        
    TO_DRILL = 3
    DRILLING = 4
    TO_OUT = 5

class IndexLine(Machine):
    '''Controls the Index Line.'''
    '''
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

        self.position = 1

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def run(self, with_mill=False, with_drill=False, as_thread=True):
        '''Runs the Index Line routine.
        
        Args:
            with_mill (bool): Product goes through mill.
            with_drill (bool): Product goes through drill.
            as_thread (bool): Runs the function as a thread.
        '''      
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(with_mill, with_drill, False), name=self.name)
            self.thread.start()
            return

        self.switch_state(State.START)
        try:
            cb_mill = Conveyor(self.revpi, self.name + "_CB_MILL", self.line_name)
            pusher_in = Actuator(self.revpi, self.name + "_PUSH1", self.line_name)
            pusher_out = Actuator(self.revpi, self.name + "_PUSH2", self.line_name)

            # move pusher to back
            pusher_in.run_to_sensor("BWD", self.name + "_REF_SW_PUSH1_BACK", timeout_in_s=5, as_thread=True) 
            pusher_out.run_to_sensor("BWD", self.name + "_REF_SW_PUSH2_BACK", timeout_in_s=5, as_thread=True)

            # Move product to Mill
            self.switch_state(State.TO_MILL)
            cb_start = Conveyor(self.revpi, self.name + "_CB_START", self.line_name)

            
            # move product to pusher_in
            cb_start.run_to_stop_sensor("", self.name + "_SENS_PUSH1", stop_delay_in_ms=750, as_thread=False)
            pusher_in.run_to_sensor("FWD", self.name + "_REF_SW_PUSH1_FRONT", timeout_in_s=5, as_thread=True) 
            cb_mill.run_to_stop_sensor("", self.name + "_SENS_MILL", as_thread=False)
            # move pusher back to back
            pusher_in.join()
            pusher_in.run_to_sensor("BWD", self.name + "_REF_SW_PUSH1_BACK", timeout_in_s=5, as_thread=True)
            
            if with_mill:
                # Milling
                self.switch_state(State.MILLING)
                Actuator(self.revpi, self.name + "_MILL_MOTOR", self.line_name).run_for_time("", self.__TIME_MILLING)


            cb_drill = Conveyor(self.revpi, self.name + "_CB_DRILL", self.line_name)

            # Move product to Drill
            self.switch_state(State.TO_DRILL)
            cb_mill.run_to_stop_sensor("", self.name + "_SENS_DRILL", as_thread=True)
            cb_drill.run_to_stop_sensor("", self.name + "_SENS_DRILL", as_thread=False)

            cb_mill.join()
            pusher_in.join()
            del pusher_in
            del cb_mill


            self.start_next_machine = True
            if with_drill:
                # Drilling
                self.switch_state(State.DRILLING)
                Actuator(self.revpi, self.name + "_DRILL_MOTOR", self.line_name).run_for_time("", self.__TIME_DRILLING)


            # Move product to Out
            self.switch_state(State.TO_OUT)
            cb_end = Conveyor(self.revpi, self.name + "_CB_END", self.line_name)

            # move product to pusher_out
            cb_drill.run_for_time("", 1.5, as_thread=False)
            # push product to out
            pusher_out.join()
            pusher_out.run_to_sensor("FWD", self.name + "_REF_SW_PUSH2_FRONT", timeout_in_s=5, as_thread=True) 
            cb_end.run_to_stop_sensor("", self.name + "_SENS_END", stop_delay_in_ms=1000, as_thread=True)
            
            # move pusher back to back
            pusher_out.join()
            pusher_out.run_to_sensor("BWD", self.name + "_REF_SW_PUSH2_BACK", timeout_in_s=5, as_thread=True)
            pusher_out.join()
            cb_end.join()

            del cb_drill
            del pusher_out
            del cb_end
            
        except SensorTimeoutError as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.position += 1
            self.switch_state(MainState.END)
