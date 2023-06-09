'''This module controls the Gripper Robots, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading

from logger import log
from sensor import Sensor
from actuator import Actuator
from robot_3d import Robot3D, Position, State


class GripRobot(Robot3D):
    '''Controls the Gripper Robot
    
    init(): Move to init position.
    move_to_position(): Moves to given position.
    '''
    GRIPPER_CLOSED = 12
    GRIPPER_OPENED = 8
    def __init__(self, revpi, name: str, moving_position: Position):
        '''Initializes the Gripper Robot.
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :moving_position: Positions that the axes should be to allow save moving
        '''
        super().__init__(revpi, name, moving_position)

        # change encoder to counter
        self.encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_COUNTER")
        self.move_threshold_hor = 2

        # get encoder and motor for claw
        self.encoder_claw = Sensor(self.revpi, self.name + "_CLAW_COUNTER")
        self.motor_claw = Actuator(self.revpi, self.name, pwm=None, type="claw")

        log.debug("Created Gripper Robot: " + self.name)


    def __del__(self):
        log.debug("Destroyed Gripper Robot: " + self.name)


    def grip(self, as_thread=True):
        '''Grip Product.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.grip, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            log.info(f"{self.name} :Gripping")
            self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_CLOSED)
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1


    def release(self, as_thread=True):
        '''Release product.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.release, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            log.info(f"{self.name} :Releasing")
            self.motor_claw.run_to_encoder_value("OPEN", self.encoder_claw, self.GRIPPER_OPENED)
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1


    def reset_claw(self, as_thread=True):
        '''Reset claw to init position.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.reset_claw, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            self.motor_claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.encoder_claw)
            self.motor_claw.run_to_encoder_value("CLOSE", self.encoder_claw, self.GRIPPER_OPENED)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
