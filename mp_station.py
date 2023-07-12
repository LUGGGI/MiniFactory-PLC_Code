'''This module controls the Multi Purpose Station, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.12"

import threading
from time import sleep
from enum import Enum, auto

from logger import log
from machine import Machine
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    INIT = 0  
    START = auto() 
    OVEN = auto() 
    TO_TABLE = auto() 
    TO_SAW = auto() 
    SAWING = auto() 
    TO_CB = auto() 
    CB = auto() 
    END = 100
    ERROR = 999

class MPStation(Machine):
    '''Controls the Multi Purpose Station.

    run(): Runs the Multi Purpose Station routine.
    '''
    __TIME_OVEN = 2
    __TIME_SAW = 2

    def __init__(self, revpi, name: str, mainloop_name: str):
        '''Initializes the Multi Purpose Station
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :mainloop_name: name of current mainloop
        '''
        super().__init__(revpi, name, mainloop_name)

        global log
        log = log.getChild(f"{self.mainloop_name}(Mps)")

        log.debug("Created Multi Purpose Station: " + self.name)

    def __del__(self):
        log.debug("Destroyed Multi Purpose Station: " + self.name)


    def init(self, as_thread=True):
        '''Move to init position'''
        if as_thread == True:
            self.thread = threading.Thread(target=self.init, args=(False,), name=self.name+"_INIT")
            self.thread.start()
            return
        try:
            Actuator(self.revpi, self.name + "_VG").run_to_sensor("TO_TABLE", self.name + "_REF_SW_VG_TABLE")
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage = 1

    def run(self, with_oven=True, as_thread=True):
        '''Runs the Punching Maschine routine.
        
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(with_oven, False), name=self.name)
            self.thread.start()
            return
        
        self.state = self.switch_state(State.START)
        try:
            compressor = Actuator(self.revpi, self.name + "_COMPRESSOR")
            vg_motor = Actuator(self.revpi, self.name + "_VG")
            vg_motor.run_to_sensor("TO_OVEN", self.name + "_REF_SW_VG_OVEN", as_thread=True) # move vg to oven

            if with_oven:
                # Move oven tray into oven and close door
                self.state = self.switch_state(State.OVEN)
                tray = Actuator(self.revpi, self.name + "_OVEN_TRAY")
                oven_door_valve = Actuator(self.revpi, self.name + "_VALVE_OVEN_DOOR")

                compressor.run_for_time("", 0.5, as_thread=True)
                oven_door_valve.start() # open door
                # sleep(0.2)
                tray.run_to_sensor("IN", self.name + "_REF_SW_OVEN_TRAY_IN") # move tray in
                oven_door_valve.stop() # close door
                compressor.join()
                Actuator(self.revpi, self.name + "_LIGHT_OVEN").run_for_time("", self.__TIME_OVEN) # turn light on for time
                compressor.run_for_time("", 0.5, as_thread=True)
                oven_door_valve.start() # open door
                tray.run_to_sensor("OUT", self.name + "_REF_SW_OVEN_TRAY_OUT") # move tray out
                del tray
                oven_door_valve.stop() # close door
                del oven_door_valve
                compressor.join()

            vg_motor.join()


            # move product to table with vacuum gripper
            self.state = self.switch_state(State.TO_TABLE)
            vg_valve = Actuator(self.revpi, self.name + "_VALVE_VG_VACUUM")
            vg_lower_valve = Actuator(self.revpi, self.name + "_VALVE_VG_LOWER")
            table = Actuator(self.revpi, self.name + "_TABLE", self.name + "_TABLE_PWM")

            table.run_to_sensor("CCW", self.name + "_REF_SW_TABLE_VG", as_thread=True) # move table to vg

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


            table.join()
            # rotate table to saw
            self.state = self.switch_state(State.TO_SAW)
            table.set_pwm(75)
            table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_SAW")


            # sawing
            self.state = self.switch_state(State.SAWING)
            Actuator(self.revpi, self.name + "_SAW").run_for_time("", self.__TIME_SAW)


            # move product to cb
            self.state = self.switch_state(State.TO_CB)
            table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_CB") # rotate table to cb
            compressor.run_for_time("", 0.5, as_thread=True)
            Actuator(self.revpi, self.name + "_VALVE_TABLE_PISTON").run_for_time("", 0.5)
            compressor.join()
            del compressor
            table.run_to_sensor("CCW", self.name + "_REF_SW_TABLE_VG", as_thread=True) # move table back to vg


            self.start_next_machine = True
            # run cb
            self.state = self.switch_state(State.CB)
            Conveyor(self.revpi, self.name + "_CB").run_to_stop_sensor("FWD", "MPS_SENS_CB", as_thread=False)
            table.join()
            del table

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1

    def run_to_out(self, as_thread=True):
        '''Runs the Conveyor to move the product out.
        
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run_to_out, args=(False, ), name=self.name)
            self.thread.start()
            return
        
        try:
            self.state = self.switch_state(State.CB)
            Conveyor(self.revpi, self.name + "_CB").run_to_stop_sensor("FWD", "CB1_SENS_START", as_thread=False)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.end_machine = True
            self.stage += 1
