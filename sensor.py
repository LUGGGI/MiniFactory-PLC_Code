'''
This module handles communication with sensors

Author: Lukas Beck
Date: 18.04.2023
'''
import inspect
from revpimodio2 import RevPiModIO, BOTH
from logger import log

product_detected = False

class Sensor():
    '''Monitoring of senors'''
    def __init__(self, revpi: RevPiModIO, name: str, edge=BOTH):
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