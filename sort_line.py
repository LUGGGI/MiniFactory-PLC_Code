'''
This module controls the Sorting Line, it inherits from machine

Author: Lukas Beck
Date: 20.05.2023
'''
import threading
from time import sleep
from enum import Enum

from logger import log
from sensor import Sensor
from machine import Machine
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    COLOR_SENSING = 1
    SORTING = 2   
    END = 100
    ERROR = 999

class IndexLine(Machine):
    '''Controls the Sorting Line

    run(): Runs the Sorting Line routine.
    '''


    def __init__(self, revpi, name: str):
        '''Initializes the Sorting Line
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        
        log.debug("Created Sorting Line: " + self.name)
    

    def __del__(self):
        log.debug("Destroyed Sorting Line: " + self.name)


    def run(self, as_thread=False):
        '''Runs the Sorting Line routine.
        
        :as_thread: Runs the function as a thread
        '''      
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(), name=self.name)
            self.thread.start()
            return
        
        try:
            compressor = Actuator(self.revpi, self.name + "_COMPRESSOR")
            cb = Conveyor(self.revpi, self.name + "_CB_FWD")

            # Color Sensing
            self.state = self.switch_state(State.COLOR_SENSING)

            # TODO: Handle color sensing
            color_sensor = Sensor(self.revpi, self.name + "_COLOR_SENSOR")


            # move product through color sensor
            cb.run_to_stop_sensor("", self.name + "_CB_SENS_PISTON")

            log.info(self.name + ": Color detected: " + color)
            color = "WHITE"

            # SORTING
            self.state = self.switch_state(State.SORTING)
            # determine sorting position
            position = 0
            if color == "WHITE":
                position = 10
            elif color == "RED":
                position = 20
            elif color == "BLUE":
                position = 30
            
            compressor.start("")
            # run to desired bay
            cb.run_to_counter_value("", self.name + "_CB_COUNTER", position)
            # push into bay
            Actuator(self.revpi, self.name + "_VALVE_PISTON_" + color).run_for_time("", 1)
            compressor.stop("")
            # check if in bay
            if Sensor(self.revpi, self.name + "_SENS_" + color).detect() == False:
                # If False that means there is a product
                log.info(self.name + ": Product sorted into: " + color)
            else:
                raise(Exception("Product not in right bay"))

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True    