'''
This module controls the 3D Gripper Robot, it inherits from machine

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
    INIT = 0
    END = 100
    ERROR = 999

class GripRobot(Machine):
    '''Controls the Gripper Robot'''

    

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)
        self.state = None
        log.debug("Created Gripper Robot: " + self.name)

    def __del__(self):
        log.debug("Destroyed Gripper Robot: " + self.name)

    def init(self):
        '''Moves the Gripper robot into his init position'''
        # call this function again as a thread
        if threading.current_thread().name != self.name + "_INIT":
            threading.Thread(target=self.init, args=(), name=self.name + "_INIT").start()
            return
        
        self.state = self.switch_state(State.INIT)
        motor = Motor(self.revpi, self.name)
        motor.run_to_sensor("BWD", self.name + "_REV_SW_HORIZONTAL")
        motor.run_to_sensor("UP", self.name + "_REV_SW_VERTICAL")
        motor.run_to_sensor("CW", self.name + "_REV_SW_ROTATION")

        log.info("Gripper Robot in init position")

    def run(self):
        if threading.current_thread().name != self.name:
            threading.Thread(target=self.init, args=(), name=self.name).start()
            return

