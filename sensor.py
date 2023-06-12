'''This module handles communication with Sensors'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

from re import T
import time
from enum import Enum
from revpimodio2 import RevPiModIO, BOTH

from logger import log

detection = False

class SensorType(Enum):
    LIGHT_BARRIER = 0
    REF_SWITCH = 1
    ENCODER = 2
    COUNTER = 3

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
    CYCLE_TIME = 0.005 # s
    counter_offset = 0
    encoder_trigger_threshold = 30

    def __init__(self, revpi: RevPiModIO, name: str, type: SensorType=None):
        '''Initializes the Sensor
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :type: Type of the sensor, if empty type is determined from name
        '''
        self.name = name
        self.type = type
        self.__revpi = revpi

        if type == None:
            if self.name.find("SENS") != -1:
                self.type = SensorType.LIGHT_BARRIER
            if self.name.find("REF_SW") != -1:
                self.type = SensorType.REF_SWITCH
            if self.name.find("ENCODER") != -1:
                self.type = SensorType.ENCODER
            if self.name.find("COUNTER") != -1:
                self.type = SensorType.COUNTER
                self.encoder_trigger_threshold = 1

        log.debug(f"Created Sensor({self.type.name}): {self.name}")


    def __del__(self):
        log.debug(f"Destroyed Sensor({self.type.name}): {self.name}")


    def get_current_value(self):
        '''Returns the current value of the sensor.
        
        Returns True if detection at LIGHT_BARRIER or REF_SWITCH
        '''
        if self.type == SensorType.ENCODER:
            return int(self.__revpi.io[self.name].value)
        
        elif self.type == SensorType.COUNTER:
            return int(self.__revpi.io[self.name].value - self.counter_offset)
        
        elif self.type == SensorType.LIGHT_BARRIER:
            return bool(not self.__revpi.io[self.name].value)
        
        else:
            # self.type == SensorType.REF_SWITCH
            return bool(self.__revpi.io[self.name].value)


    def start_monitor(self, edge=BOTH):
        '''Start monitoring sensor for detection.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        '''
        try:
            self.__revpi.io[self.name].reg_event(event_det_at_sensor, edge=edge)
        except RuntimeError:
            log.debug(f"{self.name} :Already monitoring")


    def remove_monitor(self, edge=BOTH):
        '''Stop monitoring sensor.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        '''
        self.__revpi.io[self.name].unreg_event(event_det_at_sensor, edge=edge)
        global detection
        detection = False


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
        '''Waits for detection at sensor.
        
        :edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2)
        :timeout_in_s: Time after which an exception is raised

        -> Panics if timeout is reached (no detection happened)
        '''
        if self.type == SensorType.LIGHT_BARRIER and self.get_current_value() == True or self.type == SensorType.REF_SWITCH and self.get_current_value() == True:
            log.info(f"{self.name} :Already detected")
            return

        if self.__revpi.io[self.name].wait(edge=edge, timeout=timeout_in_s*1000) == False:
            # sensor detected product
            log.info(f"{self.name} :Detection") 
        else:
            raise(Exception(f"{self.name} :No detection"))


    def wait_for_encoder(self, trigger_value: int, timeout_in_s=10) -> int:
        '''Waits for the encoder/counter to reach the trigger_value.
        
        :trigger_value: The value the motor would end up if it started from reverence switch
        :timeout_in_s: Time after which an exception is raised
        
        -> Returns reached encoder_value
        -> Panics if timeout is reached (no detection happened) or encoder value negativ
        '''
        current_value = self.get_current_value()
        if current_value > 10000:
            raise(Exception(f"{self.name} :Encoder had overflow"))
        
        start_time = time.time()
        lower = True if trigger_value < current_value else False

        while (time.time() <= start_time + timeout_in_s):
            new_value = self.get_current_value()

            if self.type == SensorType.COUNTER and lower:
                if new_value == current_value + 1:
                    self.counter_offset += 2
                    new_value = current_value = self.get_current_value()
                elif new_value > current_value:
                    raise(Exception(f"{self.name} :Counter jumped values"))


            if abs(self.get_current_value() - trigger_value) <= self.encoder_trigger_threshold:

                log.info(f"{self.name} :Value reached: {new_value}")
                return self.get_current_value() 
            
            # wait for next cycle
            time.sleep(self.CYCLE_TIME)
            
        raise(Exception(f"{self.name} :Timeout occurred"))


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


def event_det_at_sensor(io_name, __):
    '''Set detection to True'''
    log.info(f"{io_name} :Detection")
    global detection 
    detection = True    
