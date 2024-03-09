'''This module handles communication with Sensors'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.21"

import time
from enum import Enum
from revpimodio2 import RevPiModIO, BOTH

from lib.logger import log

detection = False

class SensorType(Enum):
    LIGHT_BARRIER = 0
    REF_SWITCH = 1
    ENCODER = 2
    COUNTER = 3

class Sensor():
    '''Control-methods for Senors.'''
    '''
    Methodes:
        get_current_value(): Returns the current value of the sensor.
        start_monitor(): Start monitoring sensor for detection.
        remove_monitor(): Stop monitoring sensor.
        is_detected(): Returns True if product was detected. If True removes monitor.
        wait_for_detect(): Waits for detection at sensor.
        wait_for_encoder(): Waits for the encoder/counter to reach the trigger_value.
        reset_encoder(): Resets the encoder or counter to 0.
    Attributes:
        CYCLE_TIME (int): how often encoder/counter ar checked for new values.
        __revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
        name (str): Exact name of the sensor in PiCtory.
        line_name (str): Name of current line.
        type (SensorType): Type of the sensor.
        counter_offset (int): Offset for counter so that counter can be used like encoder.
        log (Logger): Log object to print to log.
    '''
    CYCLE_TIME = 0.005 # s


    def __init__(self, revpi: RevPiModIO, name: str, line_name: str, type: SensorType=None):
        '''Initializes Sensor.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the Sensor in PiCtory.
            line_name (str): Name of current line.
            type (SensorType): Type of the sensor, if empty type is determined from name.
        '''
        self.__revpi = revpi
        self.name = name
        self.line_name = line_name
        self.type = type

        self.counter_offset = 0

        if type == None:
            if self.name.find("SENS") != -1:
                self.type = SensorType.LIGHT_BARRIER
            if self.name.find("REF_SW") != -1:
                self.type = SensorType.REF_SWITCH
            if self.name.find("ENCODER") != -1:
                self.type = SensorType.ENCODER
            if self.name.find("COUNTER") != -1:
                self.type = SensorType.COUNTER

        global log
        self.log = log.getChild(f"{self.line_name}(Sens)")

        self.log.debug(f"Created Sensor({self.type.name}): {self.name}")


    def __del__(self):
        self.log.debug(f"Destroyed {type(self).__name__}({self.type.name}): {self.name}")


    def get_current_value(self):
        '''Get the current value of the sensor.
        
        Returns:
            Value depending on SensorType.
            True if detection at LIGHT_BARRIER or REF_SWITCH.
            Int value of ENCODER or COUNTER.
        '''
        if self.type == SensorType.ENCODER:
            value = self.__revpi.io[self.name].value
        
        elif self.type == SensorType.COUNTER:
            value = self.__revpi.io[self.name].value - self.counter_offset
        
        elif self.type == SensorType.LIGHT_BARRIER:
            value = not self.__revpi.io[self.name].value
        
        else:
            # self.type == SensorType.REF_SWITCH
            value = self.__revpi.io[self.name].value

        self.log.debug(f"Got {self.type.name} value: {value}")
        return value


    def start_monitor(self, edge=BOTH):
        '''Start monitoring sensor for detection.
        
        Args:
            edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).
        '''
        try:
            self.__revpi.io[self.name].reg_event(event_det_at_sensor, edge=edge)
        except RuntimeError:
            self.log.debug(f"{self.name} already monitoring")


    def remove_monitor(self, edge=BOTH):
        '''Stop monitoring sensor.
        
        Args:
            edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).
        '''
        self.__revpi.io[self.name].unreg_event(event_det_at_sensor, edge=edge)
        global detection
        detection = False


    def is_detected(self, edge=BOTH) -> bool:
        '''Check if product was detected. If True removes monitor.

        Args:
            edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).
        Returns:
            True if product was detected, else false.
        '''
        if detection:
            self.remove_monitor(edge)
            return True
        else:
            return False


    def wait_for_detect(self, edge=BOTH, timeout_in_s=10):
        '''Waits for detection at sensor.
        
        Args:
            edge: trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).
            timeout_in_s (int): Time after which an exception is raised.
        Raises: 
            SensorTimeoutError: Timeout is reached (no detection happened)
        '''
        if self.get_current_value() == True:
            self.log.info(f"{self.name} already detected")
            return

        if self.__revpi.io[self.name].wait(edge=edge, timeout=timeout_in_s*1000) == False:
            # sensor detected product
            self.log.info(f"{self.name} detection") 
        else:
            raise(SensorTimeoutError(f"{self.name} no detection in time"))


    def wait_for_encoder(self, trigger_value: int, trigger_threshold: int, timeout_in_s=10) -> int:
        '''Waits for the encoder/counter to reach the trigger_value.
        
        Args:
            trigger_value (int): The value the motor would end up if it started from reverence switch.
            trigger_threshold (int):  The value around the trigger_value where a trigger can happen.
            timeout_in_s (int): Time after which an exception is raised.
        Returns:
            Reached encoder_value
        Raises:
            SensorTimeoutError: Timeout is reached (no detection happened).
            EncoderOverflowError: Encoder value negative.
            ValueError: Counter jumped values.
        '''
        old_value = self.get_current_value()
        if old_value > 10000:
            raise(EncoderOverflowError(f"{self.name} :Encoder had overflow"))
        
        start_time = time.time()
        lower = True if trigger_value < old_value else False

        while (time.time() <= start_time + timeout_in_s):
            new_value = self.get_current_value()

            if self.type == SensorType.COUNTER:
                # Handles counters, because they don't know the direction of the motor an offset is added if the motor is running backwards. This allows the use of counters as encoders
                if new_value == old_value + 1:
                    if lower:
                        self.counter_offset += 2
                    new_value = old_value = self.get_current_value()
                elif new_value > old_value:
                    self.log.exception(ValueError(f"{self.name} :Counter jumped values"))
                    difference = new_value - old_value - 1
                    if lower:
                        self.counter_offset += 2 + difference
                    else:
                        self.counter_offset += difference
                    new_value = old_value = self.get_current_value()

            if abs(new_value - trigger_value) <= trigger_threshold:

                self.log.info(f"{self.name} Value reached {new_value}")
                return self.get_current_value() 
            
            # wait for next cycle
            time.sleep(self.CYCLE_TIME)
            
        raise(SensorTimeoutError(f"{self.name} :Value {trigger_value} not reached in time"))


    def reset_encoder(self):
        '''Resets the encoder or counter to 0.
        
        Raises:
            TimeoutError: Encoder/counter could not be reset in time")
        '''
        for i in range(30):
            self.__revpi.io[self.name].reset()
            # wait until the actuator has stopped
            time.sleep(0.06)
            if self.__revpi.io[self.name].value == 0:
                self.log.info(f"Reset encoder: {self.name}")
                self.counter_offset = 0
                return
        raise(TimeoutError(f"{self.name} :Could not be reset in time"))


def event_det_at_sensor(io_name, __):
    '''Set detection to True'''
    log.info(f"{io_name} :Detection")
    global detection 
    detection = True    


class EncoderOverflowError(ValueError):
    '''Encoder had a 'negative' value.'''

class SensorTimeoutError(TimeoutError):
    '''Timeout occurred while waiting for Sensor.'''

class NoDetectionError(ValueError):
    '''No detection at Sensor.'''
