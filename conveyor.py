'''
This module controls a conveyor it inherits form machine

Author: Lukas Beck
Date: 10.04.2023
'''

from machine import Machine
from enum import Enum

class State(Enum):
    START = 0
    TRANSPORT = 1
    END = 2
    ERROR = 3

class Direction(Enum):
    FORWARD = 0
    BACKWARD = 1

class Conveyor(Machine):
    '''Controls a conveyor
        Back: where the motor sits
        Forward: away form Back (motor)
    '''

    state = State.START
    time_to_run = 10
    sensor_front = False
    sensor_back = False

    def __init__(self, direction):
        super().__init__(self.time_to_run)
        self.direction = direction

        print("Created Conveyor")

        self.run()

    def run(self):
        '''Runs in an loop until the product is at the end'''
        
        if self.direction is Direction.FORWARD:
            print("Run motor forward")
        else:
            print("Run motor backward")
        self.state = State.TRANSPORT
        print(self.state)
        
        while(self.state != State.END and self.state != State.ERROR):
            self.update_sensors()
            if self.sensor_back and self.get_run_time() > (self.time_to_run / 2):
                self.state = State.ERROR
                break
            
            if self.sensor_front:
                self.state = State.END
                break

            if self.get_run_time() > (self.time_to_run * 2):
                self.state = State.ERROR
                break
        
        if self.state == State.END:
            self.waiting_for_transport = True
            print("End of Conveyor")
        
        if self.state == State.ERROR:
            self.error_no_product_found = True
            print("Error in conveyor")


    def update_sensors(self):
        print("get sensor value")
        self.sensor_front = True



conv1 = Conveyor(Direction.FORWARD)