'''
This module handles communication with sensors

Author: Lukas Beck
Date: 18.04.2023
'''
import inspect
import revpimodio2
from time import sleep
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
    
    def monitor(self):
        '''monitors the sensor and updates the value'''
        revpimodio2.RevPiModIO.io[self.name].reg_event(self.update, [edge=FALLING])
        a: revpimodio2.helper.Event.wait() = revpimodio2.RevPiModIO.io[self.name]

    def update(self, _io_name, _io_value):
        '''updates the value with the state of the sensor'''
        self.__value = revpimodio2.RevPiModIO.io[self.name].value


    
    def wait_for_detection(self, timeout: int):
        '''returns True if product is detected:
        False: timeout (in s) was reached
        Debug: returns true after 1s'''
        # result = revpimodio2.RevPiModIO.io[self.name].wait([edge=revpimodio2.FALLING, exitevent=None, okvalue=None, timeout=timeout]) 

        sleep(1)
        result = 0

        if result <= 0:
            return True
        else:
            return False
        
    

def get_source() -> str:
    name = str(inspect.stack()[3][4][0]).strip()
    file = str(inspect.stack()[3][1]).rpartition("\\")[2]
    line = str(inspect.stack()[3][2])
    return "<" + file + ">(" + line + ") " + name