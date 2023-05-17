'''
This module controls the Gripper Robots, it inherits from Robot3D

Author: Lukas Beck
Date: 17.05.2023
'''
import threading
from enum import Enum

from logger import log
from sensor import Sensor
from motor import Motor
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
    
    init(): Move to init position
    move_to_position(): Moves to given position
    '''
    GRIPPER_CLOSED = 15
    GRIPPER_OPENED = 9
    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)
        self.state = None

        # get encoder and motor for claw
        self.encoder_claw = Sensor(self.revpi, self.name + "_CLAW_COUNTER")
        self.motor_claw = Motor(self.revpi, self.name, "claw")

        log.debug("Created Gripper Robot: " + self.name)

    def __del__(self):
        log.debug("Destroyed 3D Robot: " + self.name)

    def init(self, as_thread=False):
        '''Move to init position.
        
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(), name=self.name + "_init")
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)
        try:
            # move to init position
            self.move_all_axes(Position(-1,-1,1400), as_thread=False)
            self.move_all_axes(Position(0,0,0), as_thread=True)
            # move claw to init position
            self.motor_claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.encoder_claw)
            self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_OPENED)
        except Exception as error:
            self.error_exception_in_machine = True
            log.exception(error)

        log.info("Moved to init position: " + self.name)

    def move_to_position(self, position: Position, at_product=False, over_init_position=False, as_thread=False):
        '''Moves to the given position.

        :position: (rotation, horizontal, vertical): int
        :at_product: Robot will grip a product bevor moving
        :over_init_position: Robot will move to init position bevor moving to given position
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(position, at_product), name=self.name)
            self.thread.start()
            return
        
        if over_init_position:
            self.init()
            if self.error_exception_in_machine: # exception happened in init
                return

        # grip product
        if at_product:
            self.state = self.switch_state(State.GRIPPING)
            try:
                self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_CLOSED)
            except Exception as error:
                self.error_exception_in_machine = True
                log.exception(error)
                return
        try:
            # move to vertical moving position
            self.state = self.switch_state(State.TO_MOVING)
            self.move_all_axes(Position(-1, -1, 1400))
            # move rotation and horizontal axes
            self.state = self.switch_state(State.MOVING)
            self.move_all_axes(Position(position.rotation, position.horizontal, -1))
            # move down to destination
            self.state = self.switch_state(State.TO_DESTINATION)
            self.move_all_axes(Position(-1, -1, position.vertical))

            # release product
            self.state = self.switch_state(State.RELEASE)
            self.motor_claw.run_to_encoder_value("OPEN", self.encoder_claw, self.GRIPPER_OPENED)
        except Exception as error:
            self.error_exception_in_machine = True
            log.exception(error)

        self.state = self.switch_state(State.END)
        log.info("Position reached: " + str(position))

        # if moved product
        if at_product:
            self.ready_for_transport = True
