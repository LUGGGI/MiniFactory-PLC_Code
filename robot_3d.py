'''This module controls the 3D Robots, it inherits from Machine'''

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
    INIT = 0
    TO_MOVING = 1
    MOVING = 2
    TO_DESTINATION = 3
    GRIPPING = 4
    RELEASE = 5
    END = 100
    ERROR = 999

class Position:
    '''Holds a int value for each axis'''
    def __init__(self, rotation: int, horizontal: int, vertical: int) -> None:
        self.rotation = rotation
        self.horizontal = horizontal
        self.vertical = vertical

    def __str__(self) -> str:
        return f"(r:{self.rotation}, h:{self.horizontal}, v:{self.vertical})"  

class Robot3D(Machine):
    '''Controls the 3D Robot.
    
    init(): Move to init position.
    move_to_position(): Moves to given position.
    move_all_axes(): Makes linear move to give position.
    '''

    def __init__(self, revpi, name: str, moving_position: Position):
        '''Initializes the 3D Robot
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.moving_position = moving_position
        self.state = None

        # set move thresholds 
        self.move_threshold_rot = 40
        self.move_threshold_hor = 40
        self.move_threshold_ver = 40

        # get encoder
        self.encoder_rot = Sensor(self.revpi, self.name + "_ROTATION_ENCODER")
        self.encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_ENCODER")
        self.encoder_ver = Sensor(self.revpi, self.name + "_VERTICAL_ENCODER")

        # get motors
        self.motor_rot = Actuator(self.revpi, self.name, "rotation")
        self.motor_hor = Actuator(self.revpi, self.name, "horizontal")
        self.motor_ver = Actuator(self.revpi, self.name, "vertical")

        log.debug("Created 3D Robot: " + self.name)

    def __del__(self):
        log.debug("Destroyed 3D Robot: " + self.name)

    
    def init(self, to_end=False, as_thread=False):
        '''Move to init position.
        
        :to_end: set end_machine to True after completion of init
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(to_end, ), name=self.name + "_INIT")
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)
        log.info(f"Initializing {self.name}, moving to init position")
        try:
            # move to init position
            self.move_all_axes(Position(-1,0,0), as_thread=False)
            self.move_all_axes(Position(0,0,0), as_thread=True)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1
            if to_end:
                self.end_machine = True

    def move_to_position(self, position: Position, grip_bevor_moving=False, ignore_moving_pos=False, as_thread=False):
        '''Moves to the given position.

        :position: (rotation, horizontal, vertical): int
        :at_product: Robot will grip a product bevor moving
        :grip_bevor_moving: Gripper will grip product bevor moving
        :ignore_moving_pos: Robot won't move to moving Position
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(position, grip_bevor_moving, ignore_moving_pos), name=self.name)
            self.thread.start()
            return
        
        log.info(f"{self.name} :Moving to Position: {position}")
        try:
            if grip_bevor_moving:
                self.grip() # from subclass

            if not ignore_moving_pos:
                # move to moving position
                self.state = self.switch_state(State.TO_MOVING)
                self.move_all_axes(self.moving_position)

                # move non moving position axes
                self.state = self.switch_state(State.MOVING)
                # only move axis if there was no moving position for axis
                rotation = position.rotation if self.moving_position.rotation == -1 else -1
                horizontal = position.horizontal if self.moving_position.horizontal == -1 else -1
                vertical = position.vertical if self.moving_position.vertical == -1 else -1
                self.move_all_axes(Position(rotation, horizontal, vertical))

            # move to destination
            self.state = self.switch_state(State.TO_DESTINATION)
            self.move_all_axes(position)

            if grip_bevor_moving:
                self.release() # from subclass

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.info(f"{self.name} :Position reached: {position}")
            self.state = self.switch_state(State.END)
            self.stage += 1


    def move_all_axes(self, position: Position, as_thread=False):
        '''Makes linear move to given position, set a axis to -1 to not move that axis.

        :position: (rotation, horizontal, vertical): int
        :as_thread: Runs the function as a thread

        -> Panics if axes movements did not complete
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_all_axes, args=(position,), name=self.name)
            self.thread.start()
            return
        
        log.info(f"{self.name} :Moving axes to: {position}")
        # get current position
        current_position = Position(
            self.encoder_rot.get_encoder_value(),
            self.encoder_hor.get_encoder_value(),
            self.encoder_ver.get_encoder_value()
        )

        # get motor directions
        dir_rot = "CCW"
        dir_hor = "FWD"
        dir_ver = "DOWN"
        if position.rotation <= current_position.rotation:
            dir_rot = "CW"
        if position.horizontal <= current_position.horizontal:
            dir_hor = "BWD"
        if position.vertical <= current_position.vertical:
            dir_ver = "UP"

        
        # move to position
        self.motor_rot.move_axis(dir_rot, position.rotation, current_position.rotation, self.move_threshold_rot, self.encoder_rot, self.name + "_REF_SW_ROTATION", timeout_in_s=20, as_thread=True)
        self.motor_hor.move_axis(dir_hor, position.horizontal, current_position.horizontal, self.move_threshold_hor, self.encoder_hor, self.name + "_REF_SW_HORIZONTAL", as_thread=True)
        self.motor_ver.move_axis(dir_ver, position.vertical, current_position.vertical, self.move_threshold_ver, self.encoder_ver, self.name + "_REF_SW_VERTICAL", as_thread=True)

        # wait for end of each move
        try:
            self.motor_rot.thread.join()
        except:
            pass
        try:
            self.motor_hor.thread.join()
        except:
            pass
        try:
            self.motor_ver.thread.join()
        except:
            pass

        log.info(f"{self.name} :Axes moved to: {position}")
  