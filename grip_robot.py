'''This module controls the Gripper Robots, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.08"

import threading

from logger import log
from sensor import Sensor, SensorType
from actuator import Actuator
from robot_3d import Robot3D, Position, State


class GripRobot(Robot3D):
    '''Controls the Gripper Robot
    
    grip(): Grip Product.
    release(): Release Product.
    reset_claw(): Reset claw to init position.
    '''

    def __init__(self, revpi, name: str, mainloop_name: str, moving_position: Position):
        '''Initializes the Gripper Robot.
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :mainloop_name: name of current mainloop
        :moving_position: Positions that the axes should be to allow save moving
        '''
        super().__init__(revpi, name, mainloop_name, moving_position)
        self.GRIPPER_CLOSED = 13
        self.GRIPPER_OPENED = 9
        
        global log
        self.log = log.getChild(f"{self.mainloop_name}(Grip)")

        # change encoder to counter
        self._Robot3D__encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_COUNTER", self.mainloop_name, SensorType.COUNTER)
        self._Robot3D__MOVE_THRESHOLD_HOR = 2

        # get encoder and motor for claw
        self.__encoder_claw = Sensor(self.revpi, self.name + "_CLAW_COUNTER", self.mainloop_name, SensorType.COUNTER)
        self.__motor_claw = Actuator(self.revpi, self.name, self.mainloop_name, type="claw")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def grip(self, as_thread=True):
        '''Grip Product.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.grip, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            self.switch_state(State.GRIPPING)
            self.__motor_claw.run_to_encoder_value("CLOSE", self.__encoder_claw, self.GRIPPER_CLOSED, timeout_in_s=5)
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
        else:
            self.position += 1


    def release(self, as_thread=True):
        '''Release product.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.release, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            self.switch_state(State.RELEASE)
            self.__motor_claw.run_to_encoder_value("OPEN", self.__encoder_claw, self.GRIPPER_OPENED, timeout_in_s=5)
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
        else:
            self.position += 1


    def reset_claw(self, as_thread=True):
        '''Reset claw to init position.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.reset_claw, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            self.__motor_claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.__encoder_claw)
            self.__motor_claw.run_to_encoder_value("CLOSE", self.__encoder_claw, self.GRIPPER_OPENED)

        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
