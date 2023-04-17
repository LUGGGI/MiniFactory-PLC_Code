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
    INIT = 0
    START = 1
    TRANSPORT = 2        
    END = 20
    ERROR = 30

class Direction(Enum):
    FORWARD = 0
    BACKWARD = 1

class Conveyor(machine.Machine):
    '''Controls a conveyor
        Back: where the motor sits
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

        self.run()

    def run(self):
        '''Runs in an loop until the product is at the end'''
        
        if self.direction is Direction.FORWARD:
            log.warning("Run motor forward")
            sleep(1)
        else:
            log.warning("Run motor backward")
            sleep(1)

        self.state = self.switch_state(State.TRANSPORT)

        
        while(self.state != State.END and self.state != State.ERROR):
            self.update_sensors()
            if self.sensor_back and self.get_run_time() > (self.time_to_run / 2):
                self.state = self.switch_state(State.ERROR)
                break
            
            if self.sensor_front:
                self.state = self.switch_state(State.END)
                break

            if self.get_run_time() > (self.time_to_run * 2):
                self.state = self.switch_state(State.ERROR)
                break
        
        if self.state == State.END:
            self.waiting_for_transport = True
            log.info("End of Conveyor")
        
        if self.state == State.ERROR:
            self.error_no_product_found = True
            log.error("Error in conveyor")


    def update_sensors(self):
        log.warning("get sensor value")
        self.sensor_front = True
