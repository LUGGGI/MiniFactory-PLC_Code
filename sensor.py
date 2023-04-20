'''
This module handles communication with sensors

Author: Lukas Beck
Date: 18.04.2023
'''
import inspect
from logger import log

class Sensor():
    __value = False
    __was_true = False
    def __init__(self, name: str):
        self.name = name

        log.debug("Created Sensor: " + name)

    def get_value(self, was_true_enable=False) -> bool:
        '''returns the value of the sensor (True/False)
        was_true_enable: Sensor returns true if it was ever true
        Debug: returns true'''
        self.__value = True # _DEBUG

        # Save if True
        if not self.__was_true and self.__value:
            self.__was_true = True

        if was_true_enable:
            value = self.__was_true
        else:
            value = self.__value
            
        log.warning("--get value for sensor " + self.name + ": " + str(value) + ", for " 
                    + get_source())
        return value
    

def get_source() -> str:
    name = str(inspect.stack()[3][4][0]).strip()
    file = str(inspect.stack()[3][1]).rpartition("\\")[2]
    line = str(inspect.stack()[3][2])
    return "<" + file + ">(" + line + ") " + name