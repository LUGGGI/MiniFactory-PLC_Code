'''This module handles communication with Actuators'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.09"

import threading
import time
from revpimodio2 import RevPiModIO

from logger import log
from sensor import Sensor

detection = False

class Actuator():
    '''Control for Actuators, can also call Sensors
    
    run_to_sensor(): Run Actuator until product is detected.
    run_for_time(): Run Actuator for certain amount of time.
    run_to_encoder_value(): Run Actuator until the trigger_value of encoder is reached.
    run_to_encoder_start(): Run Actuator to the encoder reference switch and resets the counter to 0.
    move_axis(): Moves an axis to the given trigger value.
    start(): Start actuator.
    stop(): Stop actuator.
    set_pwm: Set PWM to percentage.
    '''
    thread = None
    PWM_TRIGGER_THRESHOLD = 17


    def __init__(self, revpi: RevPiModIO, name: str, pwm: str=None, type: str=None):
        '''Initializes the Actuator
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :pwm: Name of PWM-pin, Slows motor down, bevor reaching the value
        :type: specifier for motor name
        '''
        self.name = name
        self.__revpi = revpi
        self.pwm = pwm
        self.type = ("_" + type) if type else ""

        log.debug("Created Actuator: " + self.name + self.type)


    def __del__(self):
        log.debug("Destroyed Actuator: " + self.name + self.type)


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
            self.thread = threading.Thread(target=self.run_to_sensor, args=(direction, stop_sensor, stop_delay_in_ms, timeout_in_s), name=actuator)
            self.thread.start()
            return

        log.info(f"{actuator} :Actuator running to sensor: {stop_sensor}")

        sensor = Sensor(self.__revpi, stop_sensor)
        # check if already at stop sensor
        try:
            sensor.wait_for_detect(0)
        except:
            pass
        else:
            return


        #start actuator
        if self.pwm:
            self.set_pwm(100)
        self.start(direction)

        try:
            Sensor(self.__revpi, stop_sensor).wait_for_detect(timeout_in_s=timeout_in_s)
            time.sleep(stop_delay_in_ms/1000)
        except:
            raise
        finally:
            #stop actuator
            self.stop(direction)
            if self.pwm:
                self.set_pwm(0)


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
            self.thread = threading.Thread(target=self.run_for_time, args=(direction, wait_time_in_s, check_sensor, False), name=actuator)
            self.thread.start()
            return

        log.info(f"{actuator} :Actuator running for time: {wait_time_in_s}")

        #start actuator
        if self.pwm:
            self.set_pwm(100)
        self.start(direction)
        
        if check_sensor:
            # register event on sensor
            sensor = Sensor(self.__revpi, check_sensor)
            sensor.start_monitor()

        time.sleep(wait_time_in_s) # Wait for given time
        log.info(f"{actuator} :Run time reached")

        #stop actuator
        self.stop(direction)
        if self.pwm:
            self.set_pwm(0)

        if check_sensor and sensor.is_detected() == False:
            raise(Exception(f"{check_sensor} :No detection"))


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
            self.thread = threading.Thread(target=self.run_to_encoder_value, args=(direction, encoder, trigger_value, timeout_in_s, False), name=actuator)
            self.thread.start()
            return

        log.info(f"{actuator} :Actuator running to value: {trigger_value}, at: {encoder.name}")

        #start actuator
        if self.pwm:
            self.set_pwm(100)
            encoder.encoder_trigger_threshold = self.PWM_TRIGGER_THRESHOLD
        self.start(direction)

        try:
            if self.pwm:
                if abs(encoder.get_current_value() - trigger_value) > 100:
                    # run most of the way at full power
                    encoder.wait_for_encoder(trigger_value-100, timeout_in_s)
                # run at 15% speed for last 100 values    
                self.set_pwm(15)

            # run to trigger_value
            log.info(f"{actuator} :Stopped at: {encoder.wait_for_encoder(trigger_value, timeout_in_s)}")

        except:
            raise
        finally:
            #stop actuator
            self.stop(direction)
            if self.pwm:
                self.set_pwm(0)


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
            self.thread = threading.Thread(target=self.run_to_encoder_start, args=(direction, stop_sensor, encoder, timeout_in_s, False), name=actuator)
            self.thread.start()
            return

        log.info(f"{actuator} :Actuator running to encoder start")
        try:
            self.run_to_sensor(direction, stop_sensor, timeout_in_s)
            encoder.reset_encoder()
        except:
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
        # if trigger_value (position) is -1 do not move that axis
        if trigger_value == -1:
            return
        # if trigger value is 0 move to init position
        if trigger_value == 0:
            self.run_to_encoder_start(direction, ref_sw, encoder, timeout_in_s, as_thread)
        # if trigger value is the same as the current value don't move
        elif abs(current_value - trigger_value) < move_threshold:
            log.info(f"{self.name}_{direction} :Axis already at value")
        # move to value
        else:
            self.run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s, as_thread)


    def start(self, direction: str=""):
        '''Start Actuator.
        
        :direction: Motor direction, (last part of whole name)
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        log.info(f"{actuator} :Started actuator")
        if self.pwm:
            self.set_pwm(100)
        self.__revpi.io[actuator].value = True 


    def stop(self, direction: str=""):
        '''Stop Actuator.
        
        :direction: Motor direction, (last part of whole name)
        '''
        actuator = self.name + ( "_" + direction if direction != "" else "")
        log.info(f"{actuator} :Stopped actuator")
        if self.pwm:
            self.set_pwm(0)
        self.__revpi.io[actuator].value = False

    
    def set_pwm(self, percentage: int):
        '''Set PWM to percentage.
        
        :percentage: speed of motor, (0..100) on is over 15
        '''
        if percentage < 0 or percentage > 100:
            raise(Exception(f"{self.pwm}: {percentage} :Out of range (0-100)"))
        
        log.info(f"{self.pwm} :Set to {percentage}%")
        self.__revpi.io[self.pwm].value = percentage
