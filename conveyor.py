'''This module controls a Conveyor, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.12"

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
    '''Controls a conveyor. If conveyor isn't run with end_machine=True, the flag has to be set manually
    
    run_to_stop_sensor(): Runs the Conveyor until the product has reached the stop sensor
    run_to_counter_value(): Runs the Conveyor until the trigger_value of encoder is reached
    '''

    def __init__(self, revpi, name: str, mainloop_name: str):
        '''Initializes the Sensor
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :mainloop_name: name of current mainloop
        '''
        super().__init__(revpi, name, mainloop_name)
        self.stage = 1
        self.exception = None

        global log
        self.log = log.getChild(f"{self.mainloop_name}(Conv)")

        self.log.debug("Created Conveyor: " + self.name)


    def __del__(self):
        self.log.debug("Destroyed Conveyor: " + self.name)


    def run_to_stop_sensor(self, direction: str, stop_sensor: str, start_sensor: str=None, stop_delay_in_ms=0, timeout_in_s=10, end_machine=False, as_thread=True):
        '''Runs the Conveyor until the product has reached the stop sensor.
        
        :direction: Conveyor direction, (last part of whole name)
        :stop_sensor: Stops Conveyor if detection occurs at this Sensor
        :start_sensor: Waits with starting until detection occurs at Sensor
        :stop_delay_in_ms: Runs for given ms after detection of stop_sensor
        :timeout_in_s: Time after which an exception is raised
        :end_machine: Ends the machine if this function completes, set to false to keep machine 
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_stop_sensor, args=(direction, stop_sensor, start_sensor, stop_delay_in_ms, timeout_in_s, end_machine, False), name=self.name)
            self.thread.start()
            return
        
        self.log.warning(f"{self.name} :Running to: {stop_sensor}")
        if start_sensor != None:
            # wait for start sensor to detect product
            self.switch_state(State.WAIT)
            Sensor(self.revpi, start_sensor, self.mainloop_name).wait_for_detect(timeout_in_s=(timeout_in_s//2))
        
        self.switch_state(State.RUN)
        try:
            motor = Actuator(self.revpi, self.name, self.mainloop_name)
            motor.run_to_sensor(direction, stop_sensor, stop_delay_in_ms, timeout_in_s)
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            if self.name.find("_") != -1: # if called from another module
                if self.thread:
                    self.exception = error
                else:
                    raise
            else:
                self.log.exception(error)
        else:
            self.log.warning(f"{self.name} :Reached: {stop_sensor}")
            self.ready_for_transport = True
            if end_machine:
                self.end_machine = True
                self.switch_state(State.END)
            else:
                self.stage += 1


    def run_to_counter_value(self, direction: str, counter: str, trigger_value: int, timeout_in_s=10, end_machine=False, as_thread=True):
        '''Runs the Conveyor until the trigger_value of encoder is reached.
        
        :direction: Actuator direction, (last part of whole name)
        :counter: Counter sensor that is checked with trigger_value
        :trigger_value: Value at which to stop Conveyor
        :timeout_in_s: Time after which an exception is raised
        :end_machine: Ends the machine if this function completes, set to false to keep machine 
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_counter_value, args=(direction, counter, trigger_value, timeout_in_s, end_machine, False), name=self.name)
            self.thread.start()
            return

        self.log.warning(f"{self.name} :Running to value: {trigger_value} at {counter}")
        self.switch_state(State.RUN)
        try:
            encoder = Sensor(self.revpi, counter, self.mainloop_name)
            encoder.reset_encoder()
            Actuator(self.revpi, self.name, self.mainloop_name).run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s)
            
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            if self.name.find("_") != -1: # if called from another module
                if self.thread:
                    self.exception = error
                else:
                    raise
            else:
                self.log.exception(error)
        else:
            self.log.warning(f"{self.name} :Reached value: {trigger_value} at {counter}")
            self.ready_for_transport = True
            if end_machine:
                self.end_machine = True
                self.switch_state(State.END)
            else:
                self.stage += 1

    def join(self):
        '''Joins the current thread and reraise Exceptions'''
        self.thread.join()
        if self.exception:
            raise self.exception