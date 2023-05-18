'''
This module handles communication with motor

Author: Lukas Beck
Date: 29.04.2023
'''
import threading
import time
from revpimodio2 import RevPiModIO

from logger import log
from sensor import Sensor

product_detected = False

class Motor():
    '''Control for motors and associated sensors and reference switches'''
    thread = None
    def __init__(self, revpi: RevPiModIO,  name: str, type=""):
        self.name = name
        self.revpi = revpi
        if type != "":
            self.type = "_" + type
        else:
            self.type = type

        log.debug("Created Motor: " + self.name + self.type)

    def __del__(self):
        log.debug("Destroyed Motor: " + self.name + self.type)

    def run_to_sensor(self, direction: str, stop_sensor: str, stop_delay_in_ms=0, timeout_in_s=10, as_thread=False):
        '''Run motor until product is detected by sensor, panics if nothing was detected'''
        motor = self.name + "_" + direction
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_sensor, args=(direction, stop_sensor, stop_delay_in_ms, timeout_in_s), name=motor)
            self.thread.start()
            return

        # check if stop_sensor is a reverence switch and already pressed
        if stop_sensor.find("REF_SW") != -1 and self.revpi.io[stop_sensor].value == True:
            log.info("Detection already at stop position: " + stop_sensor + ", for: " + motor)
            return

        #start motor
        self.start(direction)

        try:
            Sensor(self.revpi, stop_sensor).wait_for_detect(timeout_in_s)
            time.sleep(stop_delay_in_ms/1000)
        except:
            raise
        finally:
            #stop motor
            self.stop(direction)

    def run_to_encoder_value(self, direction: str, encoder: Sensor, trigger_value: int, timeout_in_s=20, as_thread=False):
        '''run the motor until the trigger_value is reached

            encoder: has to be a Sensor object
            trigger_value: The value the motor would end up if it started from reverence switch'''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_encoder_value, args=(direction, encoder, trigger_value, timeout_in_s, False), name=self.name + "_" + direction)
            self.thread.start()
            return

        #start motor
        self.start(direction)

        try:
            encoder.wait_for_encoder(trigger_value, timeout_in_s)
        except:
            raise
        finally:
            #stop motor
            self.stop(direction)

    def run_to_encoder_start(self, direction: str, stop_sensor: str, encoder: Sensor, timeout_in_s=10, as_thread=False):
        '''runs to the encoder reverence switch and resets the counter to 0
        
            encoder: has to be a Sensor object'''
        motor = self.name + "_" + direction
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_encoder_start, args=(direction, stop_sensor, encoder, timeout_in_s, False), name=motor)
            self.thread.start()
            return

        try:
            self.run_to_sensor(direction, stop_sensor, timeout_in_s, as_thread=False)
        except:
            raise

        encoder.reset_encoder()
        log.info("Reset encoder motor: " + motor)


    def run_for_time(self, direction: str, check_sensor: str, wait_time_in_s):
        '''Run motor for certain amount of time, checks with sensor if product was ever detected'''

        #start motor
        self.start(direction)
        
        if check_sensor:
            # register event on sensor
            sens = Sensor(self.revpi, check_sensor)
            sens.start_monitor()

        time.sleep(wait_time_in_s) # Wait for given time

        #stop motor
        self.stop(direction)

        if check_sensor:
            if sens.is_detected() == False:
                raise(Exception("No product detected at: " + check_sensor + ", stopped motor: " + self.name + "_" + direction))
            
        log.info("Run time reached and product detected at: " + str(check_sensor) + ", stopped motor: " + self.name + "_" + direction)

    def start(self, direction: str):
        '''Start Motor
        
        :direction: Motor direction, (everything after {NAME}_)
        '''
        motor = self.name + "_" + direction
        log.info("Started motor: " + motor)
        self.revpi.io[motor].value = True 

    def stop(self, direction: str):
        '''Stop Motor
        
        :direction: Motor direction, (everything after {NAME}_)
        '''
        motor = self.name + "_" + direction
        log.info("Started motor: " + motor)
        self.revpi.io[motor].value = False 
