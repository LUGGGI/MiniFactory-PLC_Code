'''This module controls the Gripper Robots, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.02.02"

import threading
from time import sleep

from lib.logger import log
from lib.sensor import Sensor, SensorType
from lib.actuator import Actuator, SensorTimeoutError, EncoderOverflowError
from lib.robot_3d import Robot3D, Position, State, GetProductError


class GripRobot(Robot3D):
    '''Controls the Gripper Robot.'''
    '''
    Methodes:
        grip(): Grip Product.
        release(): Release Product.
        reset_claw(): Reset claw to init position.
    Attributes:
        GRIPPER_CLOSED (int): Value at which the gripper is closed.
        GRIPPER_OPENED (int): Value at which the gripper is opened.
        __encoder_claw (Sensor): Encoder (counter) for claw.
        __motor_claw (Actuator): Motor for claw.
    '''

    def __init__(self, revpi, name: str, line_name: str, moving_position: Position):
        '''Initializes the Gripper Robot.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name: Exact name of the machine in PiCtory (everything before first '_').
            line_name: Name of current line.
            moving_position (Position): Position at which the axes should be to allow save moving.
        '''
        super().__init__(revpi, name, line_name, moving_position)
        self.GRIPPER_CLOSED = 13
        self.GRIPPER_OPENED = 9
        
        global log
        self.log = log.getChild(f"{self.line_name}(Grip)")

        # change encoder to counter
        self._Robot3D__encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_COUNTER", self.line_name, SensorType.COUNTER)
        self._Robot3D__MOVE_THRESHOLD_HOR = 2

        # get encoder and motor for claw
        self.__encoder_claw = Sensor(self.revpi, self.name + "_CLAW_COUNTER", self.line_name, SensorType.COUNTER)
        self.__motor_claw = Actuator(self.revpi, self.name, self.line_name, type="claw")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def grip(self, as_thread=True):
        '''Grip Product.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.grip, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            self.switch_state(State.GRIPPING)
            self.__motor_claw.run_to_encoder_value("CLOSE", self.__encoder_claw, self.GRIPPER_CLOSED, timeout_in_s=5)

        except (SensorTimeoutError, ValueError, EncoderOverflowError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.position += 1


    def release(self, with_check_sens: str=None, as_thread=True):
        '''Release product.
        
        Args:
            with_check_sens(str): If a Sensor name is provided the sensor will be checked for detection. If False the griper resets so start.
            as_thread (bool): Runs the function as a thread.
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.release, args=(with_check_sens, False,), name=self.name)
            self.thread.start()
            return

        try:
            self.switch_state(State.RELEASE)
            self.__motor_claw.run_to_encoder_value("OPEN", self.__encoder_claw, self.GRIPPER_OPENED, timeout_in_s=5)
            
            if with_check_sens:
                sleep(0.5)
            super().release(with_check_sens)

        except (SensorTimeoutError, ValueError, EncoderOverflowError, GetProductError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.position += 1


    def reset_claw(self, as_thread=True):
        '''Reset claw to init position.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.reset_claw, args=(False,), name=self.name)
            self.thread.start()
            return

        try:
            self.__motor_claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.__encoder_claw)
            self.__motor_claw.run_to_encoder_value("CLOSE", self.__encoder_claw, self.GRIPPER_OPENED)
        
        except (SensorTimeoutError, ValueError, EncoderOverflowError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
