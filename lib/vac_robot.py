'''This module controls the Vacuum Robot, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.02.02"

import threading
from time import sleep

from lib.logger import log
from lib.actuator import Actuator
from lib.robot_3d import Robot3D, Position, State, GetProductError, ObstructionError


class VacRobot(Robot3D):
    '''Controls the Vacuum Robot'''
    '''
    Methodes:
        grip(): Grip Product.
        release(): Release Product.
    Attributes:
        __compressor (Actuator): Compressor for vacuum gripper.
        __valve (Actuator): valve for vacuum gripper.
    '''

    def __init__(self, revpi, name: str, line_name: str, moving_position=Position(-1, -1, 1400)):
        '''Initializes the Vacuum Robot.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name: Exact name of the machine in PiCtory (everything before first '_').
            line_name: Name of current line.
            moving_position (Position): Position at which the axes should be to allow save moving.
        '''
        super().__init__(revpi, name, line_name, moving_position)

        global log
        self.log = log.getChild(f"{self.line_name}(Vac)")

        self.__compressor = Actuator(self.revpi, self.name + "_COMPRESSOR", self.line_name)
        self.__valve = Actuator(self.revpi, self.name + "_VALVE_VACUUM", self.line_name)

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
            self.__compressor.run_for_time("", 0.3, as_thread=True)
            sleep(0.2)
            self.__valve.start()
            self.__compressor.join()

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
            self.__valve.stop()

            super().release(with_check_sens)

        except GetProductError as error:
            self.problem_handler(error)

        except Exception as error:
            self.error_handler(error)
        else:
            self.position += 1
