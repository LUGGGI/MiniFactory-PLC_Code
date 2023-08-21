'''This module handles communication with Actuators'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.24"

import threading
import time
from revpimodio2 import RevPiModIO

from logger import log
from sensor import Sensor, SensorType, SensorTimeoutError, EncoderOverflowError, NoDetectionError

class Actuator():
    '''Control for Actuators, can also call Sensors
    
    run_to_sensor(): Run Actuator until product is detected.
    run_for_time(): Run Actuator for certain amount of time.
    run_to_encoder_value(): Run Actuator until the trigger_value of encoder is reached.
    run_to_encoder_start(): Run Actuator to the encoder reference switch and resets the counter to 0.
    move_axis(): Moves an axis to the given trigger value.
    start(): Start actuator.
    stop(): Stop actuator.
    set_pwm(): Set PWM to percentage.
    '''
    __ENCODER_TRIGGER_THRESHOLD = 40
    __COUNTER_TRIGGER_THRESHOLD = 0
    __PWM_TRIGGER_THRESHOLD = 15
    __PWM_WINDOW = 300
    __PWM_DURATION = 100

    def __init__(self, revpi: RevPiModIO, name: str, mainloop_name: str, pwm: str=None, type: str=None):
        '''Initializes the Actuator
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :mainloop_name: name of current mainloop
        :pwm: Name of PWM-pin, Slows motor down, bevor reaching the value
        :type: specifier for motor name
        '''
        self.__revpi = revpi
        self.name = name
        self.mainloop_name = mainloop_name
        self.__pwm = pwm
        self.__type = ("_" + type) if type else ""

        self.__thread = None
        self.exception = None
        self.__pwm_value = 100

        global log
        self.log = log.getChild(f"{self.mainloop_name}(Act)")

        self.log.debug("Created Actuator: " + self.name + self.__type)


    def __del__(self):
        self.log.debug("Destroyed Actuator: " + self.name + self.__type)


    def run_to_sensor(self, direction: str, stop_sensor: str, stop_delay_in_ms=0, timeout_in_s=10, as_thread=False):
        '''Run Actuator until product is detected by a Sensor, panics if nothing was detected.
        
        :direction: Actuator direction, (last part of whole name)
        :stop_sensor: Stops Actuator if detection occurs at this Sensor
        :stop_delay_in_ms: Runs the Actuator this much longer after detection
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        # call this function again as a thread
        if as_thread == True:
            self.__thread = threading.Thread(target=self.run_to_sensor, args=(direction, stop_sensor, stop_delay_in_ms, timeout_in_s, False), name=actuator)
            self.__thread.start()
            return

        self.log.info(f"{actuator} run to sensor {stop_sensor}")

        try:
            sensor = Sensor(self.__revpi, stop_sensor, self.mainloop_name)

            # check if already at stop sensor
            if sensor.get_current_value() == True:
                self.log.info(f"{actuator} already at sensor {stop_sensor}")
                return

            #start actuator
            self.start(direction)

            sensor.wait_for_detect(timeout_in_s=timeout_in_s)
            time.sleep(stop_delay_in_ms/1000)
            
            #stop actuator
            self.stop(direction)
        except Exception as e:
            #stop actuator
            self.stop(direction)
            if self.__thread:
                self.exception = e
            else:
                raise


    def run_for_time(self, direction: str, wait_time_in_s: int, check_sensor: str=None, as_thread=False):
        '''Run Actuator for certain amount of time.
        
        :direction: Actuator direction, (last part of whole name)
        :wait_time_in_s: Time after which the actuator stops
        :check_sensor: If given, checks if detection occurs if not ->panics
        :as_thread: Runs the function as a thread
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        # call this function again as a thread
        if as_thread == True:
            self.__thread = threading.Thread(target=self.run_for_time, args=(direction, wait_time_in_s, check_sensor, False), name=actuator)
            self.__thread.start()
            return

        self.log.info(f"{actuator} run for time: {wait_time_in_s}")
        try:
            self.start(direction)
            
            if check_sensor:
                # register event on sensor
                sensor = Sensor(self.__revpi, check_sensor, self.mainloop_name)
                sensor.start_monitor()

            time.sleep(wait_time_in_s) # Wait for given time
            self.log.info(f"{actuator} run time reached")


            if check_sensor and sensor.is_detected() == False:
                raise(NoDetectionError(f"{check_sensor} :No detection"))
            
        except Exception as e:
            if self.__thread:
                self.exception = e
            else:
                raise
        finally:
            #stop actuator
            self.stop(direction)


    def run_to_encoder_value(self, direction: str, encoder: Sensor, trigger_value: int, timeout_in_s=20, as_thread=False):
        '''Run Actuator until the trigger_value of encoder is reached.

        :direction: Actuator direction, (last part of whole name)
        :encoder: Sensor object that is checked with trigger_value
        :trigger_value: Value at which to stop Actuator
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        # call this function again as a thread
        if as_thread == True:
            self.__thread = threading.Thread(target=self.run_to_encoder_value, args=(direction, encoder, trigger_value, timeout_in_s, False), name=actuator)
            self.__thread.start()
            return

        self.log.info(f"{actuator} run to value {trigger_value} at {encoder.name}")

        
        trigger_threshold = self.__ENCODER_TRIGGER_THRESHOLD if encoder.type == SensorType.ENCODER else self.__COUNTER_TRIGGER_THRESHOLD
        
        try:
            self.start(direction)
            
            if self.__pwm:
                trigger_threshold = self.__PWM_TRIGGER_THRESHOLD
                if abs(encoder.get_current_value() - trigger_value) > self.__PWM_WINDOW:
                    # run most of the way at full power
                    offset = -self.__PWM_DURATION if trigger_value > encoder.get_current_value() else self.__PWM_DURATION
                    encoder.wait_for_encoder(trigger_value+offset, self.__ENCODER_TRIGGER_THRESHOLD, timeout_in_s)

                # run at 20% speed for PWM_WINDOW values    
                self.set_pwm(20)
                self.start(direction)                
            
            # run to trigger_value
            self.log.info(f"{actuator} stopped at {encoder.wait_for_encoder(trigger_value, trigger_threshold, timeout_in_s)}")

        except Exception as e:
            if self.__thread:
                self.exception = e
            else:
                raise
        finally:
            #stop actuator
            self.stop(direction)
            if self.__pwm:
                self.set_pwm(100)


    def run_to_encoder_start(self, direction: str, stop_sensor: str, encoder: Sensor, timeout_in_s=10, as_thread=False):
        '''Run Actuator to the encoder reference switch and resets the encoder to 0.
        
        :direction: Actuator direction, (last part of whole name)
        :stop_sensor: Reference switch: stops Actuator if detection occurs at this Sensor
        :encoder: Sensor object that is checked with trigger_value
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        # call this function again as a thread
        if as_thread == True:
            self.__thread = threading.Thread(target=self.run_to_encoder_start, args=(direction, stop_sensor, encoder, timeout_in_s, False), name=actuator)
            self.__thread.start()
            return

        self.log.info(f"{actuator} run to encoder start")
        try:
            self.run_to_sensor(direction, stop_sensor, timeout_in_s=timeout_in_s)
            encoder.reset_encoder()

        except Exception as e:
            if self.__thread:
                self.exception = e
            else:
                raise


    def move_axis(self, direction: str, trigger_value: int, current_value: int, move_threshold: int, encoder: Sensor, ref_sw: str, timeout_in_s=10, as_thread=False):
        '''Moves an axis to the given trigger value.
        
        :direction: Actuator direction, (last part of whole name)
        :trigger_value: Encoder-Value at which the motor stops
        :current_value: Current Encoder-Value to determine if move is necessary
        :move_threshold: Value that has at min to be traveled to start the motor
        :encoder: Sensor object
        :ref_sw: Reference Switch at which the motor stops if it runs to the encoder start
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread

        -> Panics if timeout is reached (no detection happened)
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        # call this function again as a thread
        if as_thread == True:
            self.__thread = threading.Thread(target=self.move_axis, args=(direction, trigger_value, current_value, move_threshold, encoder, ref_sw, timeout_in_s, False), name=actuator)
            self.__thread.start()
            return

        try:
            # if trigger_value (position) is -1 do not move that axis
            if trigger_value == -1:
                return
            # if trigger value is 0 move to init position
            elif trigger_value == 0:
                self.run_to_encoder_start(direction, ref_sw, encoder, timeout_in_s, as_thread=False)
            # if trigger value is the same as the current value don't move
            elif abs(current_value - trigger_value) < move_threshold:
                self.log.info(f"{self.name}_{direction} :Axis already at position")
            # move to value
            else:
                self.run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s, as_thread=False)
        except Exception as e:
            if self.__thread:
                self.exception = e
            else:
                raise


    def start(self, direction: str=""):
        '''Start Actuator.
        
        :direction: Motor direction, (last part of whole name)
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        if self.__pwm:
            self.__revpi.io[self.__pwm].value = self.__pwm_value
        if self.__revpi.io[actuator].value != True:
            self.log.info(f"{actuator} start")
            self.__revpi.io[actuator].value = True 


    def stop(self, direction: str=""):
        '''Stop Actuator.
        
        :direction: Motor direction, (last part of whole name)
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        self.log.info(f"{actuator} stop")
        self.__revpi.io[actuator].value = False
        if self.__pwm:
            self.__revpi.io[self.__pwm].value = 0

    
    def set_pwm(self, percentage: int):
        '''Set PWM value to percentage.
        
        :percentage: speed of motor, (0..100) on is over 20
        '''
        if percentage < 0 or percentage > 100:
            raise(ValueError(f"{self.__pwm}: {percentage} :Out of range (0-100)"))
        
        self.log.info(f"{self.__pwm} set to {percentage}%")
        self.__pwm_value = percentage


    def join(self):
        '''Joins the current thread and raises Exceptions'''
        self.__thread.join()
        if self.exception:
            raise self.exception
