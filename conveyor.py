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
    TRANSPORT = 2        
    END = 20
    ERROR = 30


class Conveyor(machine.Machine):
    '''Controls a conveyor'''

    sensor_check_was_true = False

    def __init__(self, sensor_stop: Sensor, sensor_check: Sensor, motor: Motor, direction: Direction, max_transport_time: int):
        super().__init__()
        self.sensor_stop = sensor_stop
        self.sensor_check = sensor_check
        self.motor = motor
        self.direction = direction
        self.max_transport_time = max_transport_time

        self.state = self.switch_state(State.START)

        log.debug("Created Conveyor")

    def update(self):
        '''Call in a loop to update and change the state/action'''
        if self.state == State.START:
            self.motor.start(self.direction)
            sleep(1) # _DEBUG
            self.state = self.switch_state(State.TRANSPORT)

        if self.state == State.TRANSPORT:
            # triggers if a stop sensor is available and registered the product
            if self.sensor_stop != None and self.sensor_stop.get_value():
                self.motor.stop()
                self.state = self.switch_state(State.END)

            # triggers if no stop sensor is available and the max transport time is reached
            elif self.sensor_stop == None and self.get_state_time() > self.max_transport_time:
                self.motor.stop()
                self.state = self.switch_state(State.END)

            # error if a check sensor is available but didn't register a product bevor max transport time is reached
            elif self.sensor_check != None and not self.sensor_check.get_value(was_true_enable=True) and self.get_state_time() >= (self.max_transport_time):
                self.state = self.switch_state(State.ERROR)

            # error if no check sensor is available and two times max transport time is reached
            elif self.get_state_time() > (self.max_transport_time * 2):
                self.state = self.switch_state(State.ERROR)
        
        if self.state == State.END:
            self.waiting_for_transport = True
            log.info("End of Conveyor")
        
        if self.state == State.ERROR:
            log.error("Error in conveyor")
            self.motor.stop()
            self.error_no_product_found = True
