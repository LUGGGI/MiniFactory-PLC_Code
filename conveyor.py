'''This module controls a Conveyor, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.15"

import threading
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor, SensorTimeoutError
from actuator import Actuator


class State(Enum):
    WAIT = 0
    RUN = 1
    END = 100
    ERROR = 999


class Conveyor(Machine):
    '''Controls a conveyor. If conveyor isn't run with end_machine=True, the flag has to be set manually.
    
    Methodes:
        run_to_stop_sensor(): Runs the Conveyor until the product has reached the stop sensor
        run_to_counter_value(): Runs the Conveyor until the trigger_value of encoder is reached
    Attributes:
        exception (Exception): Holds exception if exception was raised.
    '''

    def __init__(self, revpi, name: str, line_name: str):
        '''Initializes Conveyor.
        
        Args
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the machine in PiCtory (everything bevor first '_').
            line_name (str): Name of current line.
        '''
        super().__init__(revpi, name, line_name)
        self.position = 1
        self.exception = None

        global log
        self.log = log.getChild(f"{self.line_name}(Conv)")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def run_to_stop_sensor(self, direction: str, stop_sensor: str, start_sensor: str=None, stop_delay_in_ms=0, timeout_in_s=10, end_machine=False, as_thread=True):
        '''Runs the Conveyor until the product has reached the stop sensor.
        
        Args:
            direction (str): Conveyor direction, (last part of whole name).
            stop_sensor (str): Stops Conveyor if detection occurs at this Sensor.
            start_sensor (str): Waits with starting until detection occurs at Sensor.
            stop_delay_in_ms (int): Runs for given ms after detection of stop_sensor.
            timeout_in_s (int): Time after which an exception is raised.
            end_machine (bool): Ends the machine if this function completes, set to false to keep machine.
            as_thread (bool): Runs the function as a thread.
        Raises:
            Only if called from other Machine.
            SensorTimeoutError: Timeout is reached (no detection happened).
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_stop_sensor, args=(direction, stop_sensor, start_sensor, stop_delay_in_ms, timeout_in_s, end_machine, False), name=self.name)
            self.thread.start()
            return
        
        self.log.warning(f"{self.name} :Running to: {stop_sensor}")
        try:
            if start_sensor != None:
                # wait for start sensor to detect product
                self.switch_state(State.WAIT)
                Sensor(self.revpi, start_sensor, self.line_name).wait_for_detect(timeout_in_s=(timeout_in_s//2))
            
            self.switch_state(State.RUN)
            motor = Actuator(self.revpi, self.name, self.line_name)
            motor.run_to_sensor(direction, stop_sensor, stop_delay_in_ms, timeout_in_s)

        except SensorTimeoutError as error:
            self.problem_in_machine = True
            self.__error_propagation(error)
        except Exception as error:
            self.error_exception_in_machine = True
            self.__error_propagation(error)
        else:
            self.log.warning(f"{self.name} :Reached: {stop_sensor}")
            self.position += 1
            if end_machine:
                self.end_conveyor()


    def run_to_counter_value(self, direction: str, counter: str, trigger_value: int, timeout_in_s=10, end_machine=False, as_thread=True):
        '''Runs the Conveyor until the trigger_value of encoder is reached.
        
        Args:
            direction (str): Actuator direction, (last part of whole name).
            counter (str): Counter sensor that is checked with trigger_value.
            trigger_value (int): Value at which to stop Conveyor.
            timeout_in_s (int): Time after which an exception is raised.
            end_machine (bool): Ends the machine if this function completes, set to false to keep machine.
            as_thread (bool): Runs the function as a thread.
        Raises:
            Only if called from other Machine.
            SensorTimeoutError: Timeout is reached (no detection happened).
            EncoderOverflowError: Encoder value negativ.
            ValueError: Counter jumped values.
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_counter_value, args=(direction, counter, trigger_value, timeout_in_s, end_machine, False), name=self.name)
            self.thread.start()
            return

        self.log.warning(f"{self.name} :Running to value: {trigger_value} at {counter}")
        self.switch_state(State.RUN)
        try:
            encoder = Sensor(self.revpi, counter, self.line_name)
            encoder.reset_encoder()
            Actuator(self.revpi, self.name, self.line_name).run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s)

        except SensorTimeoutError as error:
            self.problem_in_machine = True
            self.__error_propagation(error)
        except Exception as error:
            self.error_exception_in_machine = True
            self.__error_propagation(error)
        else:
            self.log.warning(f"{self.name} :Reached value: {trigger_value} at {counter}")
            self.position += 1
            if end_machine:
                self.end_conveyor()
                

    def join(self):
        '''Joins the current thread and reraise Exceptions.
        
        Raises:
            Exception: Exceptions that a thrown in thread function.
        '''
        self.thread.join()
        if self.exception:
            raise self.exception
        
    def end_conveyor(self):
        '''Ends conveyor.'''
        self.end_machine = True
        self.switch_state(State.END)

    def __error_propagation(self, error):
        '''Throws raised exceptions if called from Module is called from other Machine.
        
        Args:
            error: Error to be raised.
        '''
        self.switch_state(State.ERROR)
        if self.name.find("_") != -1: # if called from another module as a thread
            self.exception = error
            raise
        else:
            self.log.exception(error)
