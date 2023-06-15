'''This module controls a Conveyor, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator


class State(Enum):
    WAIT = 0
    RUN = 1
    END = 100
    ERROR = 999


class Conveyor(Machine):
    '''Controls a conveyor
    
    run_to_stop_sensor(): Runs the Conveyor until the product has reached the stop sensor
    run_to_counter_value(): Runs the Conveyor until the trigger_value of encoder is reached
    '''
    exception = None

    def __init__(self, revpi, name: str):
        '''Initializes the Sensor
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.stage = 1
        log.debug("Created Conveyor: " + self.name)


    def __del__(self):
        log.debug("Destroyed Conveyor: " + self.name)


    def run_to_stop_sensor(self, direction: str, stop_sensor: str, start_sensor: str=None, stop_delay_in_ms=0, timeout_in_s=10, as_thread=True):
        '''Runs the Conveyor until the product has reached the stop sensor.
        
        :direction: Conveyor direction, (last part of whole name)
        :stop_sensor: Stops Conveyor if detection occurs at this Sensor
        :start_sensor: Waits with starting until detection occurs at Sensor
        :stop_delay_in_ms: Runs for given ms after detection of stop_sensor
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_stop_sensor, args=(direction, stop_sensor, start_sensor, stop_delay_in_ms, timeout_in_s, False), name=self.name)
            self.thread.start()
            return
        
        if start_sensor != None:
            # wait for start sensor to detect product
            self.state = self.switch_state(State.WAIT)
            Sensor(self.revpi, start_sensor).wait_for_detect(timeout_in_s=(timeout_in_s//2))
        
        self.state = self.switch_state(State.RUN)
        try:
            motor = Actuator(self.revpi, self.name)
            motor.run_to_sensor(direction, stop_sensor, stop_delay_in_ms, timeout_in_s)
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            if self.name.find("_") != -1: # if called from another module
                if self.thread:
                    self.exception = error
                else:
                    raise
            else:
                log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
            self.stage += 1


    def run_to_counter_value(self, direction: str, counter: str, trigger_value: int, timeout_in_s=10, as_thread=True):
        '''Runs the Conveyor until the trigger_value of encoder is reached.
        
        :direction: Actuator direction, (last part of whole name)
        :counter: Counter sensor that is checked with trigger_value
        :trigger_value: Value at which to stop Conveyor
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_counter_value, args=(direction, counter, trigger_value, timeout_in_s, False), name=self.name)
            self.thread.start()
            return

        self.state = self.switch_state(State.RUN)
        try:
            encoder = Sensor(self.revpi, counter)
            encoder.reset_encoder()
            Actuator(self.revpi, self.name).run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s)
            
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            if self.name.find("_") != -1: # if called from another module
                if self.thread:
                    self.exception = error
                else:
                    raise
            else:
                log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
            self.stage += 1

    def join(self):
        '''Joins the current thread and raises Exceptions'''
        self.thread.join()
        if self.exception:
            raise self.exception