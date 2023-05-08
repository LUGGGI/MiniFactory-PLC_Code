'''
This module handles communication with sensors

Author: Lukas Beck
Date: 18.04.2023
'''
import inspect
import time
from enum import Enum
from typing import Counter
from revpimodio2 import RevPiModIO, BOTH
from logger import log

product_detected = False

class Type(Enum):
    SENSOR = 0
    COUNTER = 1
    ENCODER = 2

class Sensor():
    CYCLE_TIME = 0.02 # s
    counter_offset = 0
    '''Monitoring of senors'''
    def __init__(self, revpi: RevPiModIO, name: str, edge=BOTH, type=Type.SENSOR):
        self.revpi = revpi
        self.name = name
        self.edge = edge

        log.debug("Created Sensor: " + self.name)

    def __del__(self):
        log.debug("Destroyed Sensor: " + self.name)

    def start_monitor(self):
        '''Start monitoring the sensor'''
        try:
            self.revpi.io[self.name].reg_event(event_prod_det_sensor, edge=self.edge)
        except RuntimeError as error:
            log.debug(error)

    def remove_monitor(self):
        '''Stop monitoring sensor'''
        self.revpi.io[self.name].unreg_event(event_prod_det_sensor, edge=self.edge)

    def is_detected(self) -> bool:
        '''->True if product was detected'''
        if product_detected:
            self.remove_monitor()
            return True
        else:
            return False
        
    def wait_for_product(self, timeout_in_s=10):
        '''Pauses thread until a product is detected, panics if timeout is reached'''
        if self.revpi.io[self.name].wait(edge=self.edge, timeout=timeout_in_s*1000) == False:
            # sensor detected product
            log.info("Product detected at: " + self.name) 
        else:
            raise(Exception("No product found at: " + self.name))   
   
    def wait_for_encoder(self, trigger_value: int, is_counter=False, timeout_in_s=10):
        '''Pauses thread until the encoder/counter reached the trigger_value
        
        trigger_value: The value the motor would end up if it started from reverence switch'''
        counter = self.revpi.io[self.name].value
        start = time.time()
        higher = True
        # check running direction
        if trigger_value < counter - self.counter_offset :
            higher = False
            self.counter_start = counter

        while(True):
            if higher and self.revpi.io[self.name].value - self.counter_offset >= trigger_value:
                break
            elif not higher and is_counter and self.positive_to_negativ() - self.counter_offset <= trigger_value:
                break
            elif not higher and self.revpi.io[self.name].value <= trigger_value:
                break
            elif time.time() >= start + timeout_in_s:
                raise(Exception("No product found at: " + self.name))
            time.sleep(self.CYCLE_TIME)

        log.info("Count reached at: " + self.name) 
        if is_counter:
            self.counter_offset = self.revpi.io[self.name].value - trigger_value

    def positive_to_negativ(self):
        '''converts the upwards counting value to a from counter_start downwards counting value'''
        counter = self.revpi.io[self.name].value
        return counter - 2 * (counter - self.counter_start)
        
        
def event_prod_det_sensor(io_name, _io_value):
    '''set product_detected to True'''
    log.info("Product detected at: " + str(io_name))
    global product_detected 
    product_detected = True    

# debug function gets source object
def get_source() -> str:
    name = str(inspect.stack()[3][4][0]).strip()
    file = str(inspect.stack()[3][1]).rpartition("\\")[2]
    line = str(inspect.stack()[3][2])
    return "<" + file + ">(" + line + ") " + name