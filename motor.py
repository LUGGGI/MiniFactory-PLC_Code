'''
This module handles communication with motor

Author: Lukas Beck
Date: 18.04.2023
'''
from enum import Enum
import inspect
from logger import log

class Direction(Enum):
    FORWARD = 0
    BACKWARD = 1

class Motor():
    def __init__(self, name: str):
        self.name = name

        log.debug("Created Motor: " + name)

    def start(self, direction: Direction):
        '''starts the motor in the direction'''
        log.warning("--start motor: " + self.name + ", in direction=" + str(direction) + ", for " 
                    + get_source())

    def stop(self):
        '''stop motor'''
        log.warning("--stop motor: " + self.name + ", for " 
                    + get_source())
        
def get_source() -> str:
    name = str(inspect.stack()[3][4][0]).strip()
    file = str(inspect.stack()[3][1]).rpartition("\\")[2]
    line = str(inspect.stack()[3][2])
    return "<" + file + ">(" + line + ") " + name