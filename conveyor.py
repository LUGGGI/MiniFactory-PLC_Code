'''
This module controls a conveyor, it inherits form machine

Author: Lukas Beck
Date: 10.04.2023
'''
import machine
from enum import Enum
from time import sleep
from logger import log

class State(Enum):
    START = 0
    TRANSPORT = 2        
    END = 20
    ERROR = 30

class Direction(Enum):
    FORWARD = 0
    BACKWARD = 1

class Conveyor(machine.Machine):
    '''Controls a conveyor
        Backward: where the motor sits
        Forward: away form Back (motor)
    '''

    # state = State.START
    time_to_run = 10
    sensor_front = False
    sensor_back = False

    def __init__(self, direction):
        super().__init__(self.time_to_run)
        self.direction = direction
        self.state = self.switch_state(State.START)

        log.debug("Created Conveyor")

    def update(self):
        '''Call in a loop to update and change the state/action'''
        if self.state == State.START:
            if self.direction is Direction.FORWARD:
                log.warning("--Motor forward")
            else:
                log.warning("--Motor backward")

            self.state = self.switch_state(State.TRANSPORT)

        if self.state == State.TRANSPORT:
            if self.sensor_back and self.get_state_time() > (self.time_to_run / 2):
                self.state = self.switch_state(State.ERROR)
            
            if self.sensor_front:
                self.state = self.switch_state(State.END)

            if self.get_state_time() > (self.state.value * 2):
                self.state = self.switch_state(State.ERROR)
        
        if self.state == State.END:
            self.waiting_for_transport = True
            log.info("End of Conveyor")
        
        if self.state == State.ERROR:
            self.error_no_product_found = True
            log.error("Error in conveyor")

        sleep(1)
        self.update_sensors()


    def update_sensors(self):
        log.info("get sensor value")
        self.sensor_front = True
