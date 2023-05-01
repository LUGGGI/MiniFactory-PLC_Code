'''
This module handles communication with motor

Author: Lukas Beck
Date: 29.04.2023
'''

import inspect
import time
from revpimodio2 import RevPiModIO, BOTH, RISING

from logger import log
from sensor import Sensor

product_detected = False

class Motor():
    '''Control for motors and associated sensors and reference switches'''
    def __init__(self, revpi: RevPiModIO,  name: str):
        self.name = name
        self.revpi = revpi

        log.debug("Created Motor: " + self.name)

    def __del__(self):
        log.debug("Destroyed Motor: " + self.name)

    def run_to_sensor(self, direction: str, stop_sensor: str, timeout_in_s=10):
        '''Run motor until product is detected by sensor.

        ->True: Product is detected by sensor
        ->False: timeout was reached 
        '''
        motor = self.name + "_" + direction

        self.revpi.io[motor].value = True 
        log.info("Started motor: " + motor)

        if self.revpi.io[stop_sensor].wait(edge=BOTH, timeout=timeout_in_s*1000) == False:
            # sensor detected product
            self.revpi.io[motor].value = False 
            log.info("Product detected at: " + stop_sensor + ", stopped motor: " + motor)
        else:
            # product not detected and timeout reached
            self.revpi.io[motor].value = False
            raise(Exception("No product found at: " + stop_sensor + ", stopped motor: " + motor))

    def run_for_time(self, direction: str, check_sensor: str, wait_time_in_s):
        '''Run motor for certain amount of time, checks with sensor if product was ever detected
        
            pulses: Number of pulses that the motor should run for (if non provided use timeout instead)
        ->True: Product was detected while running
        ->False: Product was not detected while running
        '''
        motor = self.name + "_" + direction

        self.revpi.io[motor].value = True 
        log.info("Started motor: " + motor)

        
        if check_sensor:
            # register event on sensor
            sens = Sensor(self.revpi, check_sensor, RISING)
            sens.start_monitor()

        time.sleep(wait_time_in_s) # Wait for given time

        self.revpi.io[motor].value = False 

        if check_sensor:
            if sens.is_detected() == False:
                raise(Exception("No product detected at: " + check_sensor + ", stopped motor: " + motor))
            
        log.info("Wait time reached and product detected at: " + str(check_sensor) + ", stopped motor: " + motor)

# debug function gets source objects
def get_source() -> str:
    name = str(inspect.stack()[3][4][0]).strip()
    file = str(inspect.stack()[3][1]).rpartition("\\")[2]
    line = str(inspect.stack()[3][2])
    return "<" + file + ">(" + line + ") " + name