'''
This module controls a conveyor, it inherits form machine

Author: Lukas Beck
Date: 29.04.2023
'''
import threading
from enum import Enum
from logger import log
from motor import Motor
from machine import Machine


class State(Enum):
    START = 0     
    END = 1
    ERROR = 2


class Conveyor(Machine):
    '''Controls a conveyor'''

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)

        log.debug("Created Conveyor: " + self.name)

    def __del__(self):
        log.debug("Destroyed Conveyor: " + self.name)

    def run_to_stop_sensor(self, direction: str, sensor: str, timeout_in_s: int):
        '''Runs the conveyor until the product has reached the stop sensor'''
        # call this function again as a thread
        if threading.current_thread().name == "MainThread":
            threading.Thread(target=self.run_to_stop_sensor, args=(direction, sensor, timeout_in_s), name=self.name).start()
            return
        
        self.state = self.switch_state(State.START)
        try:
            motor = Motor(self.rev_pi, self.name)
            motor.run_to_sensor(direction, sensor, timeout_in_s)
        except Exception as error:
            log.error(error)
            self.state = self.switch_state(State.ERROR)
        else:
            self.state = self.switch_state(State.END)
        finally:
            self.end()

    def run_for_time(self, direction: str, check_sensor: str, run_for_in_s: int):
        '''Runs the conveyor for given amount of seconds, checks for product with check sensor'''
        # call this function again as a thread
        if threading.current_thread().name == "MainThread":
            threading.Thread(target=self.run_for_time, args=(direction, check_sensor, run_for_in_s), name=self.name).start()
            return

        self.state = self.switch_state(State.START)
        try:
            motor = Motor(self.rev_pi, self.name)
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

        
