'''
This module handles communication with Sensors

Author: Lukas Beck
Date: 19.15.2023
'''
import time
from revpimodio2 import RevPiModIO, BOTH

from logger import log

detection = False

class Sensor():
    CYCLE_TIME = 0.02 # s
    counter_offset = 0
    '''Control for Senors
    
    start_monitor(): Start monitoring sensor for detection.
    remove_monitor(): Stop monitoring sensor.
    is_detected(): Returns True if product was detected.
    wait_for_detect(): Pauses thread until a detection occurs.
    wait_for_encoder(): Pauses thread until the encoder/counter reached the trigger_value.
    __positive_to_negativ(): Converts the upwards counting value to a from counter_start downwards counting value.
    reset_encoder(): Resets the encoder or counter to 0.
    get_encoder_value(): Returns the current value of the encoder.
    '''

    def __init__(self, revpi: RevPiModIO, name: str):
        '''Initializes the Sensor
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :type: specifier for motor name
        '''
        self.name = name
        self.__revpi = revpi

        log.debug("Created Sensor: " + self.name)


    def __del__(self):
        log.debug("Destroyed Sensor: " + self.name)


    def start_monitor(self, edge=BOTH):
        '''Start monitoring sensor for detection.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        '''
        try:
            self.__revpi.io[self.name].reg_event(event_det_at_sensor, edge=edge)
        except RuntimeError as error:
            log.debug(error)


    def remove_monitor(self, edge=BOTH):
        '''Stop monitoring sensor.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        '''
        self.__revpi.io[self.name].unreg_event(event_det_at_sensor, edge=edge)


    def is_detected(self, edge=BOTH) -> bool:
        '''Returns True if product was detected.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        '''
        if detection:
            self.remove_monitor(edge)
            return True
        else:
            return False
        
        
    def wait_for_detect(self, edge=BOTH, timeout_in_s=10):
        '''Pauses thread until a detection occurs, panics if timeout is reached.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        :timeout_in_s: Time after which an exception is raised

        -> Panics if timeout is reached (no detection happened)
        '''
        if self.__revpi.io[self.name].wait(edge=edge, timeout=timeout_in_s*1000) == False:
            # sensor detected product
            log.info("Detection at: " + self.name) 
        else:
            raise(Exception("No detection at: " + self.name))
           
   
    def wait_for_encoder(self, trigger_value: int, timeout_in_s=10):
        '''Pauses thread until the encoder/counter reached the trigger_value.
        
        :trigger_value: The value the motor would end up if it started from reverence switch
        :timeout_in_s: Time after which an exception is raised

        -> Panics if timeout is reached (no detection happened) or encoder negativ
        '''
        counter = self.__revpi.io[self.name].value
        if counter > 10000:
            raise(Exception("Counter negativ for: " + self.name))
        
        start = time.time()
        higher = True
        # check running direction
        if trigger_value < counter - self.counter_offset :
            higher = False
            self.counter_start = counter

        while(True):
            # wait for encoder or counter to be higher than the trigger_value
            if higher and self.__revpi.io[self.name].value - self.counter_offset >= trigger_value:
                log.info("Count reached at: " + self.name + ": " + str(self.__revpi.io[self.name].value - self.counter_offset)) 
                break
            # wait for counter to be lower that trigger_value
            elif not higher and self.name.find("COUNTER") != -1 and self.__positive_to_negativ() - self.counter_offset <= trigger_value:
                log.info("Count reached at: " + self.name + ": " + str(self.__positive_to_negativ() - self.counter_offset)) 
                break
            # wait for encoder to be lower that trigger_value
            elif not higher and self.__revpi.io[self.name].value <= trigger_value:
                log.info("Count reached at: " + self.name + ": " + str(self.__revpi.io[self.name].value)) 
                break
            # check if timeout time is reached 
            elif time.time() >= start + timeout_in_s:
                raise(Exception("No detection at: " + self.name))
            
            # wait for next cycle
            time.sleep(self.CYCLE_TIME)

        # update the counter_offset
        if self.name.find("COUNTER") != -1:
            self.counter_offset = self.__revpi.io[self.name].value - trigger_value


    def __positive_to_negativ(self):
        '''Converts the upwards counting value to a from counter_start downwards counting value.'''
        counter = self.__revpi.io[self.name].value
        return counter - 2 * (counter - self.counter_start)
    

    def reset_encoder(self):
        '''Resets the encoder or counter to 0.'''
        for i in range(15):
            self.__revpi.io[self.name].reset()
            # wait until the actuator has stopped
            time.sleep(0.04)
            if self.__revpi.io[self.name].value == 0:
                break

        log.info("Reset encoder: " + self.name)


    def get_encoder_value(self):
        '''Returns the current value of the encoder.'''
        return self.__revpi.io[self.name].value - self.counter_offset
        
        
def event_det_at_sensor(io_name, _):
    '''Set detection to True'''
    log.info("Detection at: " + str(io_name))
    global detection 
    detection = True    
