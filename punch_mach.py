'''
This module controls the Punching Line with the connected conveyor, it inherits from machine

Author: Lukas Beck
Date: 01.05s.2023
'''
import threading
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor
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

    def run(self):
        if threading.current_thread().name == "MainThread":
            threading.Thread(target=self.run, args=(), name=self.name).start()
            return
        try:
            self.state = self.switch_state(State.CB_IN)
            # Move product from connected conveyor belt to inner conveyor belt
            cb = Conveyor(self.revpi, "CB2")
            cb.run_for_time("FWD", "CB2_SENS_END", 10)

            wait_for_cb = Sensor(self.revpi, "CB2_SENS_END")
            wait_for_cb.wait_for_product()

            self.state = self.switch_state(State.CB_PUNCH_TO)
            # raise puncher
            puncher = Motor(self.revpi, self.name)
            t_puncher = threading.Thread(target=puncher.run_to_sensor, args=("UP", "PM_REF_SW_TOP"), name="PM_UP")
            t_puncher.start()
            # Move product from inner conveyor belt to puncher
            cb_punch = Conveyor(self.revpi, "PM_CB")
            cb_punch.run_to_stop_sensor("FWD", "PM_SENS_PM", 10, blocking=True)

            self.state = self.switch_state(State.PUNCHING)
            log.info("Punching product")
            t_puncher.join()
            puncher.run_to_sensor("DOWN", "PM_REF_SW_BOTTOM")
            # raise puncher
            t_puncher = threading.Thread(target=puncher.run_to_sensor, args=("UP", "PM_REF_SW_TOP"), name="PM_UP2")
            t_puncher.start()

            self.state = self.switch_state(State.CB_PUNCH_FROM)
            #  Move product from puncher to connected conveyor
            cb_punch.run_for_time("BWD", "PM_SENS_IN", 10)
            wait_for_cb_punch = Sensor(self.revpi, "PM_SENS_IN")
            wait_for_cb_punch.wait_for_product()

            self.state = self.switch_state(State.CB_IN)
            # Move product to end of connected conveyor belt
            cb.run_to_stop_sensor("BWD", "CB2_SENS_START", 10, blocking=True)

            

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
