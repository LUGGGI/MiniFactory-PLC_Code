'''
This module controls the Punching Line with the connected conveyor, it inherits from machine

Author: Lukas Beck
Date: 01.05s.2023
'''
import threading
from enum import Enum

from logger import log
from machine import Machine
from motor import Motor
from conveyor import Conveyor

class State(Enum):
    CB_IN = 0   
    CB_PUNCH_TO = 1
    PUNCHING = 2
    CB_PUNCH_FROM = 3
    CB_OUT = 4  
    END = 100
    ERROR = 999

class PunchMach(Machine):

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)
        self.state = None
        log.debug("Created Punching Machine: " + self.name)

    def __del__(self):
        log.debug("Destroyed Punching Machine: " + self.name)

    def run(self, as_thread=False):
        if  as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(), name=self.name)
            self.thread.start()
            return
        try:
            self.state = self.switch_state(State.CB_IN)
            # Move product from connected conveyor belt to inner conveyor belt
            cb = Conveyor(self.revpi, "CB2")
            cb.run_to_stop_sensor("FWD", "PM_SENS_IN", "CB2_SENS_END")

            self.state = self.switch_state(State.CB_PUNCH_TO)
            # raise puncher
            puncher = Motor(self.revpi, self.name)
            puncher.run_to_sensor("UP", "PM_REF_SW_TOP", as_thread=True)
            # Move product from inner conveyor belt to puncher
            cb_punch = Conveyor(self.revpi, "PM_CB")
            cb_punch.run_to_stop_sensor("FWD", "PM_SENS_PM")

            self.state = self.switch_state(State.PUNCHING)
            log.info("Punching product")
            puncher.run_to_sensor("DOWN", "PM_REF_SW_BOTTOM")
            # raise puncher
            puncher.run_to_sensor("UP", "PM_REF_SW_TOP", as_thread=True)

            self.state = self.switch_state(State.CB_PUNCH_FROM)
            #  Move product from puncher to connected conveyor
            cb_punch.run_to_stop_sensor("BWD", "CB2_SENS_END", "PM_SENS_IN")

            self.state = self.switch_state(State.CB_IN)
            # Move product to end of connected conveyor belt
            cb.run_to_stop_sensor("BWD", "CB2_SENS_START")

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_no_product_found = True
            log.exception(error)
        else:
            del puncher
            del cb_punch
            del cb
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
