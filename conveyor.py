'''
This module controls a conveyor, it inherits from machine

Author: Lukas Beck
Date: 01.05.2023
'''
import threading
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor
from motor import Motor


class State(Enum):
    WAIT = 0
    START = 1     
    END = 100
    ERROR = 999


class Conveyor(Machine):
    '''Controls a conveyor'''

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)
        self.state = None
        log.debug("Created Conveyor: " + self.name)

    def __del__(self):
        log.debug("Destroyed Conveyor: " + self.name)

    def run_to_stop_sensor(self, direction: str, stop_sensor: str, start_sensor: str=None, timeout_in_s=10, as_thread=False):
        '''Runs the conveyor until the product has reached the stop sensor'''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_stop_sensor, args=(direction, stop_sensor, timeout_in_s), name=self.name)
            self.thread.start()
            return
        
        if start_sensor != None:
            # wait for start sensor to detect product
            Sensor(self.revpi, start_sensor).wait_for_detect()
        
        self.state = self.switch_state(State.START)
        try:
            motor = Motor(self.revpi, self.name)
            motor.run_to_sensor(direction, stop_sensor, timeout_in_s)
        except Exception as error:
            log.exception(error)
            self.state = self.switch_state(State.ERROR)
        else:
            self.state = self.switch_state(State.END)
        finally:
            self.end()

    def run_for_time(self, direction: str, check_sensor: str, run_for_in_s=5, as_thread=False):
        '''Runs the conveyor for given amount of seconds, checks for product with check sensor'''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_for_time, args=(direction, check_sensor, run_for_in_s), name=self.name)
            self.thread.start()
            return

        self.state = self.switch_state(State.START)
        try:
            motor = Motor(self.revpi, self.name)
            motor.run_for_time(direction, check_sensor, run_for_in_s)
        except Exception as error:
            log.exception(error)
            self.state = self.switch_state(State.ERROR)
        else:
            self.state = self.switch_state(State.END)
        finally:
            self.end()

    def end(self):
        '''Call in a loop to update and change the state/action'''
        
        if self.state == State.END:
            self.ready_for_transport = True
        
        elif self.state == State.ERROR:
            self.error_no_product_found = True

        
