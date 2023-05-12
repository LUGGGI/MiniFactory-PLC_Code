'''
This module controls the Gripper Robots, it inherits from Robot3D

Author: Lukas Beck
Date: 12.05.2023
'''
import threading
from enum import Enum
from time import sleep

from logger import log
from machine import Machine
from sensor import Sensor
from motor import Motor
from robot_3d import Robot3D, Position

class State(Enum):
    INIT = 0
    RUN = 1
    END = 100
    ERROR = 999

class GripRobot(Robot3D):
    '''Controls the Gripper Robot'''
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
        '''Move to init position'''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(), name=self.name + "_init")
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)

        # move to init position
        self.move_all_axes(Position(-1,-1,1400), as_thread=False)
        self.move_all_axes(Position(0,0,0), as_thread=True)
        # move claw to init position
        self.motor_claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.encoder_claw)
        self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_OPENED)

        self.thread.join()

        log.info("Moved to init position: " + self.name)

    def run(self, as_thread=False):
        '''Move a product'''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.run, args=(), name=self.name)
            self.thread.start()
            return
        self.state = self.switch_state(State.RUN)
        self.move_to_position(Position(225, 60, 2050), at_product=False)
        self.move_to_position(Position(2380, 0, 2050), at_product=True)

        self.ready_for_transport = True

    def move_to_position(self, position: Position, at_product: bool, as_thread=False):
        '''Runs to the given position\\
        position: (rotation, horizontal, vertical): int
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(position, at_product), name=self.name)
            self.thread.start()
            return
        
        # grip product
        if at_product:
            self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_CLOSED)

        # move to vertical moving position
        self.move_all_axes(Position(-1, -1, 1400))
        # move rotation and horizontal axes
        self.move_all_axes(Position(position.rotation, position.horizontal, -1))
        # move down to destination
        self.move_all_axes(Position(-1, -1, position.vertical))

        # release product
        self.motor_claw.run_to_encoder_value("OPEN", self.encoder_claw, self.GRIPPER_OPENED)

        log.info("Position reached: " + str(position))


        # # move to moving position
        # mot_ver.run_to_encoder_value(dir_ver)
        # claw.run_to_encoder_value("CLOSE", "GR1_CLAW_COUNTER", 10, as_thread=True)
        # vertical.run_to_encoder_value("DOWN", "GR1_VERTICAL_ENCODER", 1400, as_thread=True)

        

        # # move to cb1
        # rotation.run_to_encoder_value("CCW", "GR1_ROTATION_ENCODER", 190, as_thread=True)
        # horizontal.run_to_encoder_value("FWD", "GR1_HORIZONTAL_COUNTER", 60, as_thread=True)
        # rotation.thread.join()
        # vertical.thread.join()

        # # grip product
        # vertical.run_to_encoder_value("DOWN", "GR1_VERTICAL_ENCODER", 2050, as_thread=False)
        # claw.run_to_encoder_value("CLOSE", "GR1_CLAW_COUNTER", 15, as_thread=False)
        # vertical.run_to_encoder_value("UP", "GR1_VERTICAL_ENCODER", 1400, as_thread=False)

        # # move to cb3
        # # rotation.run_to_encoder_value("CCW", "GR1_ROTATION_ENCODER", 2380, as_thread=True)
        # # horizontal.run_to_encoder_value("BWD", "GR1_HORIZONTAL_COUNTER", 0, as_thread=True)
        # # rotation.thread.join()

        # # move to cb2
        # rotation.run_to_encoder_value("CCW", "GR1_ROTATION_ENCODER", 3832, as_thread=True)
        # horizontal.run_to_encoder_value("FWD", "GR1_HORIZONTAL_COUNTER", 80, as_thread=True)
        # rotation.thread.join()
        # vertical.thread.join()

        # # release product
        # vertical.run_to_encoder_value("DOWN", "GR1_VERTICAL_ENCODER", 2050, as_thread=False)
        # claw.run_to_encoder_value("OPEN", "GR1_CLAW_COUNTER", 10, as_thread=True)
        # vertical.run_to_encoder_value("UP", "GR1_VERTICAL_ENCODER", 1500, as_thread=False)
        

        # log.info("3D Robot in endposition")
        # self.ready_for_transport = True
        # return