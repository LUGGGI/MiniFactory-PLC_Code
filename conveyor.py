'''
This module controls a conveyor, it inherits form machine

Author: Lukas Beck
Date: 10.04.2023
'''
from enum import Enum
from time import sleep
from logger import log
from sensor import Sensor
from motor import Motor, Direction
import machine


class State(Enum):
    START = 0
    TRANSPORT = 0        
    END = 0
    ERROR = 0


class Conveyor(machine.Machine):
    '''Controls a conveyor'''

    def __init__(self, sensor: Sensor, motor: Motor):
        super().__init__()
        self.__sensor = sensor
        self.__motor = motor

        self.state = self.switch_state(State.START)

        log.debug("Created Conveyor")

    def run_to_sensor_stop(self, direction: Direction, max_run_time: int):
        '''runs the conveyor until the product has reached the stop sensor'''

        self.__motor.start(direction)
        if self.__sensor.wait_for_detection(timeout=max_run_time):
            self.state = self.switch_state(State.END)
        else:
            self.state = self.switch_state(State.ERROR)
        self.__motor.stop()

    def run_for_time(self, direction: Direction, run_for: int):
        '''runs the conveyor for given amount of seconds, checks for product with check sensor'''
        
        self.__motor.start(direction)

    def update(self):
        '''Call in a loop to update and change the state/action'''
        if self.state == State.START:
            self.__motor.start(self.__direction)
            sleep(1) # _DEBUG
            self.state = self.switch_state(State.TRANSPORT)

        if self.state == State.TRANSPORT:
            # triggers if a stop sensor is available and registered the product
            if self.__sensor_stop != None and self.__sensor_stop.get_value():
                self.__motor.stop()
                self.state = self.switch_state(State.END)

            # triggers if no stop sensor is available and the max transport time is reached
            elif self.__sensor_stop == None and self.get_state_time() > self.__max_transport_time:
                self.__motor.stop()
                self.state = self.switch_state(State.END)

            # error if a check sensor is available but didn't register a product bevor max transport time is reached
            elif self.__sensor_check != None and not self.__sensor_check.get_value(was_true_enable=True) and self.get_state_time() >= (self.__max_transport_time):
                self.state = self.switch_state(State.ERROR)

            # error if no check sensor is available and two times max transport time is reached
            elif self.get_state_time() > (self.__max_transport_time * 2):
                self.state = self.switch_state(State.ERROR)
        
        if self.state == State.END:
            self.waiting_for_transport = True
            log.info("End of Conveyor")
        
        if self.state == State.ERROR:
            log.error("Error in conveyor")
            self.__motor.stop()
            self.error_no_product_found = True
