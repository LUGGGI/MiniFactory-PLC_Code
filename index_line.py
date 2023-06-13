'''This module controls the Indexed Line with two Machining Stations (Mill and Drill), it inherits from machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading
from time import sleep
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    TO_MILL = 1
    MILLING = 2        
    TO_DRILL = 3
    DRILLING = 4
    TO_OUT = 5      
    END = 100
    ERROR = 999

class IndexLine(Machine):
    '''Controls the Index Line

    run(): Runs the Index Line routine.
    '''
    __TIME_MILLING = 1
    __TIME_DRILLING = 1


    def __init__(self, revpi, name: str):
        '''Initializes the Index Line
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)

        log.debug("Created Index Line: " + self.name)
    

    def __del__(self):
        log.debug("Destroyed Index Line: " + self.name)


    def run(self, as_thread=True):
        '''Runs the Index Line routine.
        
        :as_thread: Runs the function as a thread
        '''      
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            cb_mill = Conveyor(self.revpi, self.name + "_CB_MIll")

            # Move product to Mill
            self.state = self.switch_state(State.TO_MILL)
            pusher_in = Actuator(self.revpi, self.name + "_PUSH1")
            cb_start = Conveyor(self.revpi, self.name + "_CB_START")

            # move pusher to back
            pusher_in.run_to_sensor("BWD", self.name + "_REF_SW_PUSH1_BACK", as_thread=True) 
            # move product to pusher_in
            cb_start.run_to_stop_sensor("", self.name + "_REF_SW_PUSH1_FRONT", as_thread=True)
            # wait for product to be detected by sensor 
            Sensor(self.revpi, self.name + "_SENS_PUSH1").wait_for_detect()
            sleep(1) # wait for product to be in front of pusher
            # push product to cb_mill
            pusher_in.join()
            cb_start.join()
            del cb_start
            pusher_in.run_to_sensor("FWD", self.name + "_REF_SW_PUSH1_FRONT", as_thread=True) 
            cb_mill.run_to_stop_sensor("", self.name + "_SENS_MILL", as_thread=False)
            # move pusher back to back
            pusher_in.join()
            pusher_in.run_to_sensor("BWD", self.name + "_REF_SW_PUSH1_BACK", as_thread=True)
            

            # Milling
            self.state = self.switch_state(State.MILLING)
            Actuator(self.revpi, self.name + "_MILL_MOTOR").run_for_time("", self.__TIME_MILLING)


            cb_drill = Conveyor(self.revpi, self.name + "_CB_DRIll")

            # Move product to Drill
            self.state = self.switch_state(State.TO_DRILL)
            cb_mill.run_to_stop_sensor("", self.name + "_SENS_DRILL", as_thread=True)
            cb_drill.run_to_stop_sensor("", self.name + "_SENS_DRILL", as_thread=False)

            cb_mill.join()
            pusher_in.join()
            del pusher_in
            del cb_mill


            # Drilling
            self.state = self.switch_state(State.DRILLING)
            Actuator(self.revpi, self.name + "_DRILL_MOTOR").run_for_time("", self.__TIME_DRILLING)


            # Move product to Out
            self.state = self.switch_state(State.TO_OUT)
            pusher_out = Actuator(self.revpi, self.name + "_PUSH2")
            cb_end = Conveyor(self.revpi, self.name + "_CB_END")

            # move pusher to back
            pusher_out.run_to_sensor("BWD", self.name + "_REF_SW_PUSH2_BACK", as_thread=True)
            # move product to pusher_out
            cb_drill.run_to_stop_sensor("", self.name + "_REF_SW_PUSH2_FRONT", as_thread=True)
            sleep(1) # wait for product to be in front of pusher
            # push product to out
            pusher_out.thread.join()
            pusher_out.run_to_sensor("FWD", self.name + "_REF_SW_PUSH2_FRONT", as_thread=True) 
            cb_end.run_to_stop_sensor("", self.name + "_SENS_END", stop_delay_in_ms=1000, as_thread=False)
            del cb_end
            # move pusher back to back
            pusher_out.run_to_sensor("BWD", self.name + "_REF_SW_PUSH2_BACK", as_thread=True) 

            cb_drill.join()
            pusher_out.join()
            del cb_drill
            del pusher_out

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True    