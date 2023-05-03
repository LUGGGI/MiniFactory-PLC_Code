'''
This module handles communication with motor

Author: Lukas Beck
Date: 29.04.2023
'''
from email.policy import default
import threading
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

    def run_to_sensor(self, direction: str, stop_sensor: str, timeout_in_s=10, as_thread=False):
        '''Run motor until product is detected by sensor.

        ->True: Product is detected by sensor
        ->False: timeout was reached 
        '''
        motor = self.name + "_" + direction
        # call this function again as a thread
        if as_thread == True and threading.current_thread().name != motor:
            threading.Thread(target=self.run_to_sensor, args=(direction, stop_sensor, timeout_in_s), name=motor).start()
            return
        
        # check if stop_sensor is a reverence switch
        if stop_sensor.find("REF_SW") != -1 and self.revpi.io[stop_sensor].value == True:
            log.info("Detection already at stop position: " + stop_sensor + ", for: " + motor)
            return

        #start motor
        self.revpi.io[motor].value = True 
        log.info("Started motor: " + motor)

        try:
            Sensor(self.revpi, stop_sensor, BOTH).wait_for_product(timeout_in_s)
        except Exception as error:
            log.exception(error)
        finally:
            self.revpi.io[motor].value = False 
            log.info("Stopped motor: " + motor)

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
                log.exception("No product detected at: " + check_sensor + ", stopped motor: " + motor)
            
        log.info("Run time reached and product detected at: " + str(check_sensor) + ", stopped motor: " + motor)

# debug function gets source objects
def get_source() -> str:
    name = str(inspect.stack()[3][4][0]).strip()
    file = str(inspect.stack()[3][1]).rpartition("\\")[2]
    line = str(inspect.stack()[3][2])
    return "<" + file + ">(" + line + ") " + name