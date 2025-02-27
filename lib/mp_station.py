'''This module controls the Multi Purpose Station, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.12"

import threading
from time import sleep
from enum import Enum, auto

from lib.logger import log
from lib.machine import Machine, MainState
from lib.actuator import Actuator, SensorTimeoutError
from lib.conveyor import Conveyor

class State(Enum):
    INIT = 0  
    START = auto() 
    OVEN = auto() 
    TO_TABLE = auto() 
    TO_SAW = auto() 
    SAWING = auto() 
    TO_CB = auto() 
    CB = auto()

class MPStation(Machine):
    '''Controls the Multi Purpose Station.'''
    '''
    Methodes:
        init(): Move to init position.
        run(): Runs the Multi Purpose Station routine.
        run_to_out(): Runs the Conveyor to move the product out.
    Attributes:
        __TIME_OVEN (int): Time that the oven should be active.
        __TIME_SAW (int): Time that the saw should be active.
        table (Actuator): Actuator object for the table.
    '''
    __TIME_OVEN = 2
    __TIME_SAW = 2

    def __init__(self, revpi, name: str, line_name: str):
        '''Initializes the Multi Purpose Station.
        
        Args
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the machine in PiCtory (everything before first '_').
            line_name (str): Name of current line.
        '''
        super().__init__(revpi, name, line_name)
        self.table = Actuator(self.revpi, self.name + "_TABLE", self.line_name, self.name + "_TABLE_PWM")
        self.table.set_pwm(75)

        global log
        self.log = log.getChild(f"{self.line_name}(Mps)")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def init(self, as_thread=True):
        '''Move to init position.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        if as_thread == True:
            self.thread = threading.Thread(target=self.init, args=(False,), name=self.name+"_INIT")
            self.thread.start()
            return
        try:
            self.switch_state(State.INIT)
            Actuator(self.revpi, self.name + "_VG", self.line_name).run_to_sensor("TO_TABLE", self.name + "_REF_SW_VG_TABLE")

        except SensorTimeoutError as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.position = 1

    def run(self, with_oven=True, with_saw=False, as_thread=True):
        '''Runs the Multi Purpose Station routine.
        
        Args:
            with_oven (bool): Product goes through oven.
            with_saw (bool): Product goes through saw.
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(with_oven, with_saw, False), name=self.name)
            self.thread.start()
            return
        
        self.switch_state(State.START)
        try:
            compressor = Actuator(self.revpi, self.name + "_COMPRESSOR", self.line_name)
            vg_motor = Actuator(self.revpi, self.name + "_VG", self.line_name)
            vg_motor.run_to_sensor("TO_OVEN", self.name + "_REF_SW_VG_OVEN", as_thread=True) # move vg to oven

            if with_oven:
                # Move oven tray into oven and close door
                self.switch_state(State.OVEN)
                tray = Actuator(self.revpi, self.name + "_OVEN_TRAY", self.line_name)
                oven_door_valve = Actuator(self.revpi, self.name + "_VALVE_OVEN_DOOR", self.line_name)

                compressor.run_for_time("", 0.5, as_thread=True)
                oven_door_valve.start() # open door
                # sleep(0.2)
                tray.run_to_sensor("IN", self.name + "_REF_SW_OVEN_TRAY_IN") # move tray in
                oven_door_valve.stop() # close door
                compressor.join()
                Actuator(self.revpi, self.name + "_LIGHT_OVEN", self.line_name).run_for_time("", self.__TIME_OVEN) # turn light on for time
                compressor.run_for_time("", 0.5, as_thread=True)
                oven_door_valve.start() # open door
                tray.run_to_sensor("OUT", self.name + "_REF_SW_OVEN_TRAY_OUT") # move tray out
                del tray
                oven_door_valve.stop() # close door
                del oven_door_valve
                compressor.join()

            vg_motor.join()


            # move product to table with vacuum gripper
            self.switch_state(State.TO_TABLE)
            vg_valve = Actuator(self.revpi, self.name + "_VALVE_VG_VACUUM", self.line_name)
            vg_lower_valve = Actuator(self.revpi, self.name + "_VALVE_VG_LOWER", self.line_name)

            self.table.run_to_sensor("CCW", self.name + "_REF_SW_TABLE_VG", as_thread=True) # move table to vg

            vg_motor.join() # wait for the vg to be at oven
            compressor.run_for_time("", 1.5, as_thread=True)
            vg_lower_valve.run_for_time("", 1, as_thread=True) # lower gripper
            sleep(0.7)
            vg_valve.start() # create vacuum at gripper
            sleep(0.5) # wait for gripper to be at top
            compressor.join()
            vg_lower_valve.join()
            vg_motor.run_to_sensor("TO_TABLE", self.name + "_REF_SW_VG_TABLE") # move vg to table
            del vg_motor

            compressor.run_for_time("", 1, as_thread=True)
            vg_lower_valve.run_for_time("", 0.7, as_thread=True) # lower gripper
            sleep(0.5)
            vg_valve.stop() # stop vacuum at gripper
            del vg_valve
            sleep(0.5)
            compressor.join()
            vg_lower_valve.join()
            del vg_lower_valve


            self.table.join()

            if with_saw:
                # rotate table to saw
                self.switch_state(State.TO_SAW)
                self.table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_SAW")

                # sawing
                self.switch_state(State.SAWING)
                Actuator(self.revpi, self.name + "_SAW", self.line_name).run_for_time("", self.__TIME_SAW)


            # move product to cb
            self.switch_state(State.TO_CB)
            self.table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_CB") # rotate table to cb
            compressor.run_for_time("", 0.5, as_thread=True)
            Actuator(self.revpi, self.name + "_VALVE_TABLE_PISTON", self.line_name).run_for_time("", 0.5)
            compressor.join()
            del compressor
            self.table.run_to_sensor("CCW", self.name + "_REF_SW_TABLE_VG", as_thread=True) # move table back to vg


            # run cb
            self.switch_state(State.CB)
            Conveyor(self.revpi, self.name + "_CB", self.line_name).run_to_stop_sensor("FWD", "MPS_SENS_CB", as_thread=False)

        except SensorTimeoutError as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.position += 1

    def run_to_out(self, as_thread=True):
        '''Runs the Conveyor to move the product out.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_out, args=(False, ), name=self.name)
            self.thread.start()
            return
        
        try:
            self.switch_state(State.CB)
            Conveyor(self.revpi, self.name + "_CB", self.line_name).run_to_stop_sensor("FWD", "CB1_SENS_START", as_thread=False)
            
            self.table.join()
            del self.table

        except SensorTimeoutError as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.position += 1
            self.switch_state(MainState.END)
