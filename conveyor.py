'''
This module controls a conveyor, it inherits form machine

Author: Lukas Beck
Date: 29.04.2023
'''
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
        self.__motor = Motor(self.rev_pi, self.name)

        log.debug("Created Conveyor: " + self.name)

    def __del__(self):
        del self.__motor
        log.debug("Destroyed Conveyor: " + self.name)

    def run_to_stop_sensor(self, direction: str, sensor: str, timeout_in_s: int):
        '''Runs the conveyor until the product has reached the stop sensor'''
        self.state = self.switch_state(State.START)
        try:
            self.__motor.run_to_sensor(direction, sensor, timeout_in_s)
        except Exception as error:
            log.error(error)
            self.state = self.switch_state(State.ERROR)
        else:
            self.state = self.switch_state(State.END)
        finally:
            self.end()

    def run_for_time(self, direction: str, check_sensor: str, run_for_in_s: int):
        '''Runs the conveyor for given amount of seconds, checks for product with check sensor'''
        self.state = self.switch_state(State.START)
        try:
            self.__motor.run_for_time(direction, check_sensor, run_for_in_s)
        except Exception as error:
            log.error(error)
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

        
