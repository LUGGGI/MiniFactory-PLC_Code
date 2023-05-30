'''This module controls the Gripper Robots, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading
from enum import Enum

from logger import log
from sensor import Sensor
from actuator import Actuator
from robot_3d import Robot3D, Position

class State(Enum):
    INIT = 0
    TO_MOVING = 1
    MOVING = 2
    TO_DESTINATION = 3
    GRIPPING = 4
    RELEASE = 5
    END = 100
    ERROR = 999

class GripRobot(Robot3D):
    '''Controls the Gripper Robot
    
    init(): Move to init position.
    move_to_position(): Moves to given position.
    '''
    GRIPPER_CLOSED = 12
    GRIPPER_OPENED = 8
    def __init__(self, revpi, name: str, moving_position=Position(-1, -1, 1400)):
        '''Initializes the Gripper Robot.
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :moving_position: Positions that the axes should be to allow save moving
        '''
        super().__init__(revpi, name, moving_position)

        # get encoder and motor for claw
        self.encoder_claw = Sensor(self.revpi, self.name + "_CLAW_COUNTER")
        self.motor_claw = Actuator(self.revpi, self.name, "claw")

        log.debug("Created Gripper Robot: " + self.name)

    def __del__(self):
        log.debug("Destroyed Gripper Robot: " + self.name)


    def init(self, as_thread=False):
        '''Move to init position.
        
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(), name=self.name + "_INIT")
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)
        log.info(f"Initializing {self.name}, moving to init position")
        try:
            # move to init position
            self.move_all_axes(Position(-1,0,0), as_thread=False)
            self.move_all_axes(Position(0,0,0), as_thread=True)
            # move claw to init position
            self.motor_claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.encoder_claw)
            self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_OPENED)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1


    def move_to_position(self, position: Position, grip_bevor_moving=False, over_init_position=False, ignore_moving_pos=False, as_thread=False):
        '''Moves to the given position.

        :position: (rotation, horizontal, vertical): int
        :at_product: Robot will grip a product bevor moving
        :over_init_position: Robot will move to init position bevor moving to given position
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(position, grip_bevor_moving, over_init_position, ignore_moving_pos), name=self.name)
            self.thread.start()
            return
        
        log.info(f"{self.name} :Moving to Position: {position}")
        if over_init_position:
            self.init()
            if self.error_exception_in_machine: # exception happened in init
                return

        # grip product
        if grip_bevor_moving:
            self.state = self.switch_state(State.GRIPPING)
            try:
                self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_CLOSED)
            except Exception as error:
                self.state = self.switch_state(State.ERROR)
                self.error_exception_in_machine = True
                log.exception(error)
                return
        try:
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

            # release product
            self.state = self.switch_state(State.RELEASE)
            self.motor_claw.run_to_encoder_value("OPEN", self.encoder_claw, self.GRIPPER_OPENED)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.info(f"{self.name} :Position reached: {position}")
            self.state = self.switch_state(State.END)
            self.stage += 1
