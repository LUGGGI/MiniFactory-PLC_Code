'''This module handles communication with Sensors'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import time
from revpimodio2 import RevPiModIO, BOTH

from logger import log

detection = False

class Sensor():
    '''Control for Senors
    
    detect(): Returns value of Sensor
    start_monitor(): Start monitoring sensor for detection.
    remove_monitor(): Stop monitoring sensor.
    is_detected(): Returns True if product was detected.
    wait_for_detect(): Pauses thread until a detection occurs.
    wait_for_encoder(): Pauses thread until the encoder/counter reached the trigger_value.
    __positive_to_negativ(): Converts the upwards counting value to a from counter_start downwards counting value.
    reset_encoder(): Resets the encoder or counter to 0.
    get_encoder_value(): Returns the current value of the encoder.
    '''
    CYCLE_TIME = 0.02 # s
    counter_offset = 0
    encoder_pre_stop = 30

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

    
    def detect(self) -> bool:
        '''Returns value of Sensor'''
        return self.__revpi.io[self.name].value     


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
            log.info(f"{self.name} :Detection") 
        else:
            raise(Exception(f"{self.name} :No detection"))
           
   
    def wait_for_encoder(self, trigger_value: int, timeout_in_s=10):
        '''Pauses thread until the encoder/counter reached the trigger_value.
        
        :trigger_value: The value the motor would end up if it started from reverence switch
        :timeout_in_s: Time after which an exception is raised

        -> Panics if timeout is reached (no detection happened) or encoder negativ
        '''
        counter = self.__revpi.io[self.name].value
        if counter > 10000:
            raise(Exception(f"{self.name} :Counter negativ"))
        
        start = time.time()
        higher = True
        # check running direction
        if trigger_value < counter - self.counter_offset :
            higher = False
            self.counter_start = counter
        
        # stop actuator a bit bevor to account for overrun
        if self.name.find("ENCODER") != -1:
            if higher:
                trigger_value -= self.encoder_pre_stop 
            else:
                trigger_value += self.encoder_pre_stop

        while(True):
            # wait for encoder or counter to be higher than the trigger_value
            if higher and self.__revpi.io[self.name].value - self.counter_offset >= trigger_value:
                log.info(f"{self.name} :Count reached: " + str(self.__revpi.io[self.name].value - self.counter_offset)) 
                break
            # wait for counter to be lower that trigger_value
            elif not higher and self.name.find("COUNTER") != -1 and self.__positive_to_negativ() - self.counter_offset <= trigger_value:
                log.info(f"{self.name} :Count reached: " + str(self.__positive_to_negativ() - self.counter_offset)) 
                break
            # wait for encoder to be lower that trigger_value
            elif not higher and self.__revpi.io[self.name].value <= trigger_value:
                log.info(f"{self.name} :Count reached: " + str(self.__revpi.io[self.name].value)) 
                break
            # check if timeout time is reached 
            elif time.time() >= start + timeout_in_s:
                raise(Exception(f"{self.name} :Count not reached in time"))
            
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
            time.sleep(0.06)
            if self.__revpi.io[self.name].value == 0:
                log.info("Reset encoder: " + self.name)
                self.counter_offset = 0
                return
        raise(Exception(f"{self.name} :ERROR while reset"))


    def get_encoder_value(self):
        '''Returns the current value of the encoder.'''
        return self.__revpi.io[self.name].value - self.counter_offset
        
        
def event_det_at_sensor(io_name, __):
    '''Set detection to True'''
    log.info(f"{io_name} :Detection")
    global detection 
    detection = True    
