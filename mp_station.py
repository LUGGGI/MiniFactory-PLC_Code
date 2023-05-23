'''This module controls the Multi Purpose Station, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading
from time import sleep
from enum import Enum

from logger import log
from machine import Machine
from actuator import Actuator
from conveyor import Conveyor

class State(Enum):
    INIT = 0   
    OVEN = 1
    TO_TABLE = 2
    TO_SAW = 3
    SAWING = 4
    TO_CB = 5
    CB = 6  
    END = 100
    ERROR = 999

class MPStation(Machine):
    '''Controls the Multi Purpose Station.

    run(): Runs the Multi Purpose Station routine.
    '''
    
    __TIME_OVEN = 2
    __TIME_SAW = 2


    def __init__(self, revpi, name: str):
        '''Initializes the Multi Purpose Station
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.state = None
        
        log.debug("Created Multi Purpose Station: " + self.name)

    def __del__(self):
        log.debug("Destroyed Multi Purpose Station: " + self.name)


    def run(self, as_thread=False):
        '''Runs the Punching Maschine routine.
        
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread == True:
            self.thread = threading.Thread(target=self.run, args=(), name=self.name)
            self.thread.start()
            return

        try:

            # Move oven tray into oven and close door
            self.state = self.switch_state(State.OVEN)
            compressor = Actuator(self.revpi, self.name + "_COMPRESSOR")
            tray = Actuator(self.revpi, self.name + "_OVEN_TRAY")
            oven_door_valve = Actuator(self.revpi, self.name + "_VALVE_OVEN_DOOR")

            compressor.start("")
            oven_door_valve.start("") # open door
            sleep(0.2)
            tray.run_to_sensor("IN", self.name + "_REF_SW_OVEN_TRAY_IN") # move tray in
            oven_door_valve.stop("") # close door
            Actuator(self.revpi, self.name + "_LIGHT_OVEN").run_for_time("", self.__TIME_OVEN) # turn light on for time
            oven_door_valve.start("") # open door
            # sleep(0.5)
            tray.run_to_sensor("OUT", self.name + "_REF_SW_OVEN_TRAY_OUT") # move tray out
            oven_door_valve.stop("") # close door

            del tray
            del oven_door_valve


            # move product to table with vacuum gripper
            self.state = self.switch_state(State.TO_TABLE)
            vg_valve = Actuator(self.revpi, self.name + "_VALVE_VG_VACUUM")
            vg_lower_valve = Actuator(self.revpi, self.name + "_VALVE_VG_LOWER")
            vg_motor = Actuator(self.revpi, self.name + "_VG")
            table = Actuator(self.revpi, self.name + "_TABLE")

            table.run_to_sensor("CCW", self.name + "_REF_SW_TABLE_VG", as_thread=True) # move table to vg

            vg_motor.run_to_sensor("TO_OVEN", self.name + "_REF_SW_VG_OVEN") # move vg to oven
            vg_lower_valve.run_for_time("", 1) # lower gripper
            vg_valve.start("") # create vacuum at gripper
            sleep(1) # wait for gripper to be at top
            vg_motor.run_to_sensor("TO_TABLE", self.name + "_REF_SW_VG_TABLE") # move vg to table
            vg_lower_valve.run_for_time("", 1) # lower gripper
            vg_valve.stop("") # stop vacuum at gripper
            # vg_motor.run_to_sensor("TO_OVEN", self.name + "_REF_SW_VG_OVEN", as_thread=True) # move vg back to oven

            del vg_valve
            del vg_lower_valve
            del vg_motor


            # rotate table to saw
            self.state = self.switch_state(State.TO_SAW)
            table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_SAW")

            
            # sawing
            self.state = self.switch_state(State.SAWING)
            Actuator(self.revpi, self.name + "_SAW").run_for_time("", self.__TIME_SAW)


            # move product to cb
            self.state = self.switch_state(State.TO_CB)
            table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_CB") # rotate table to cb
            Actuator(self.revpi, self.name + "_VALVE_TABLE_PISTON").run_for_time("", 1)
            table.run_to_sensor("CW", self.name + "_REF_SW_TABLE_VG", as_thread=True) # move table back to vg
            compressor.stop("")

            del table
            del compressor


            # run cb
            self.state = self.switch_state(State.CB)
            Conveyor(self.revpi, self.name + "_CB").run_to_stop_sensor("FWD", self.name + "_SENS_CB")

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
