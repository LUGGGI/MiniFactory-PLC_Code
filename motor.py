'''
This module handles communication with motor

Author: Lukas Beck
Date: 29.04.2023
'''
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
        if as_thread == True:
            threading.Thread(target=self.run_to_sensor, args=(direction, stop_sensor, timeout_in_s), name=motor).start()
            return
        
        # check if stop_sensor is a reverence switch and already pressed
        if stop_sensor.find("REF_SW") != -1 and self.revpi.io[stop_sensor].value == True:
            log.info("Detection already at stop position: " + stop_sensor + ", for: " + motor)
            return

        #start motor
        log.info("Started motor: " + motor)
        self.revpi.io[motor].value = True 

        try:
            Sensor(self.revpi, stop_sensor, BOTH).wait_for_product(timeout_in_s)
        except Exception as error:
            log.exception(error)
        finally:
            log.info("Stopped motor: " + motor)
            self.revpi.io[motor].value = False 

    def run_to_count(self, direction: str, encoder: str, trigger_value: int, timeout_in_s=10, as_thread=False):
        '''run the motor until the trigger_value is reached
        
        trigger_value: The value the motor would end up if it started from reverence switch'''
        motor = self.name + "_" + direction
        # call this function again as a thread
        if as_thread == True:
            threading.Thread(target=self.run_to_sensor, args=(direction, encoder, trigger_value, timeout_in_s), name=motor).start()
            return
        
        is_counter = False
        # TODO change to COUNTER
        if encoder.find("COUNT") != -1:
            is_counter = True

        #start motor
        log.info("Started motor: " + motor)
        self.revpi.io[motor].value = True 

        try:
            Sensor(self.revpi, encoder).wait_for_encoder(trigger_value, is_counter, timeout_in_s)
        except Exception as error:
            log.exception(error)
        finally:
            log.info("Stopped motor: " + motor)
            self.revpi.io[motor].value = False 

    def run_for_time(self, direction: str, check_sensor: str, wait_time_in_s):
        '''Run motor for certain amount of time, checks with sensor if product was ever detected
        
            pulses: Number of pulses that the motor should run for (if non provided use timeout instead)
        ->True: Product was detected while running
        ->False: Product was not detected while running
        '''
        motor = self.name + "_" + direction

        log.info("Started motor: " + motor)
        self.revpi.io[motor].value = True 

        
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