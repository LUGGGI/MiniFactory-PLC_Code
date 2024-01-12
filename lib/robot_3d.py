'''This module controls the 3D Robots, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.12"

import threading
from enum import Enum

from lib.logger import log
from lib.machine import Machine, MainState
from lib.sensor import Sensor
from lib.actuator import Actuator, EncoderOverflowError, SensorTimeoutError

class State(Enum):
    INIT = 0
    TO_MOVING_POS = 1
    MOVING = 2
    TO_DESTINATION = 3
    GRIPPING = 4
    RELEASE = 5
    GET_PRODUCT = 6

class Position:
    '''Holds a int value for each axis.'''
    '''
    Attributes:
        rotation (int): Rotation position.
        horizontal (int): Horizontal position.
        vertical (int): Vertical position.
    '''
    def __init__(self, rotation: int, horizontal: int, vertical: int):
        '''Save given positions.
        
        Args:
            rotation (int): Rotation position.
            horizontal (int): Horizontal position.
            vertical (int): Vertical position.
        '''
        self.rotation = rotation
        self.horizontal = horizontal
        self.vertical = vertical

    def __str__(self) -> str:
        '''Get formatted string of positions.
        
        Returns:
            str: Formatted string of positions.
        '''
        return f"(r:{self.rotation if self.rotation != -1 else '-'}, h:{self.horizontal if self.horizontal != -1 else '-'}, v:{self.vertical if self.vertical != -1 else '-'})"  

class Robot3D(Machine):
    '''Controls the 3D Robot.'''
    '''
    Methodes:
        init(): Move to init position.
        move_to_position(): Moves to given position.
        move_all_axes(): Makes linear move to give position.
    Attributes:
        __MOVE_THRESHOLD_ROT (int): Only moves the rotation axis if movement is more.
        __MOVE_THRESHOLD_HOR (int): Only moves the horizontal axis if movement is more.
        __MOVE_THRESHOLD_VER (int): Only moves the vertical axis if movement is more.
        __MAX_PICKUP_TRIES (int): Max tries the robot can use to pickup a product.
        __moving_position (Position): Position where the axes should be to allow save moving.
        __encoder_rot (Sensor): Encoder for rotation axis.
        __encoder_hor (Sensor): Encoder for horizontal axis.
        __encoder_ver (Sensor): Encoder for vertical axis.
        pwm_rot (str): PWM name for rotation axis.
        pwm_hor (str): PWM name for horizontal axis.
        pwm_ver (str): PWM name for vertical axis.
        __motor_rot (Actuator): Motor for rotation axis.
        __motor_hor (Actuator): Motor for horizontal axis.
        __motor_ver (Actuator): Motor for vertical axis.

    '''
    __MOVE_THRESHOLD_HOR = 40
    __MOVE_THRESHOLD_VER = 40
    __MAX_PICKUP_TRIES = 3

    def __init__(self, revpi, name: str, line_name: str, moving_position: Position, move_threshold_rot: int = 40):
        '''Initializes the 3D Robot
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the machine in PiCtory (everything bevor first '_').
            line_name (str): Name of current line.
            moving_position (Position): Position where the axes should be to allow save moving.
            move_threshold_rot (int): Set the move threshold for the rotation axis (defaults to 40).
        '''
        super().__init__(revpi, name, line_name)
        self.__move_threshold_rot = move_threshold_rot

        global log
        self.log = log.getChild(f"{self.line_name}(Rob)")

        self.__moving_position = moving_position

        # get encoder
        self.__encoder_rot = Sensor(self.revpi, self.name + "_ROTATION_ENCODER", self.line_name)
        self.__encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_ENCODER", self.line_name)
        self.__encoder_ver = Sensor(self.revpi, self.name + "_VERTICAL_ENCODER", self.line_name)

        # get pwm pins
        pwm_rot = self.name + "_ROTATION_PWM"
        pwm_hor = self.name + "_HORIZONTAL_PWM" if self.name.find("VG") != -1 else None
        pwm_ver = None

        # get motors
        self.__motor_rot = Actuator(self.revpi, self.name, self.line_name, pwm=pwm_rot, type="rotation")
        self.__motor_hor = Actuator(self.revpi, self.name, self.line_name, pwm=pwm_hor, type="horizontal")
        self.__motor_ver = Actuator(self.revpi, self.name, self.line_name, pwm=pwm_ver, type="vertical")


    def init(self, to_end=False, as_thread=True):
        '''Move to init position.
        Args:
            to_end (bool): If True ends machine after completion of init.
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(to_end, False), name=self.name + "_INIT")
            self.thread.start()
            return

        self.switch_state(State.INIT)
        try:
            # move to init position
            self.__move_all_axes(Position(-1,0,0))
            self.__move_all_axes(Position(0,-1,-1))

        except (SensorTimeoutError, ValueError, EncoderOverflowError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            if to_end:
                self.switch_state(MainState.END)
            else:
                self.log.warning(f"{self.name}: Initialized")
                self.position += 1


    def get_product(self, vertical_position: int, sensor: str=None, as_thread=True):
        '''Moves to position without moving position, grips product and moves back up to original position.

        Args:
            vertical_position (int): Vertical value to move to to grip.
            sensor (str): Sensor that will be checked for detection while moving up.
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.get_product, args=(vertical_position, sensor, False), name=self.name)
            self.thread.start()
            return
        try: 
            self.switch_state(State.GET_PRODUCT)
            current_program_position = self.position
            # start position
            start_vertical_position = self.__encoder_ver.get_current_value()
            try_num = 1
            while(True):
                if self.state == MainState.PROBLEM or self.state == MainState.ERROR:
                    break
                
                # move down to product
                self.__move_all_axes(Position(-1, -1, vertical_position))
                self.grip(as_thread = False)
                # move back up
                self.__move_all_axes(Position(-1, -1, start_vertical_position))

                # check if product still at sensor, if so try to grip again
                if sensor and Sensor(self.revpi, sensor, self.line_name).get_current_value() == True:
                    self.log.warning(f"{self.name} :Product still at Sensor, try nr.: {try_num}")
                    self.reset_claw(as_thread=False)
                else:
                    # product was gripped
                    break

                # try one list time with complete robot reset.
                if try_num == self.__MAX_PICKUP_TRIES:
                    self.log.error(f"{self.name} :Product still at Sensor, grip failed, resetting position")
                    # get current position
                    current_position = Position(
                        self.__encoder_rot.get_current_value(),
                        self.__encoder_hor.get_current_value(),
                        start_vertical_position
                    )
                    # reset robot position and try again
                    self.init(as_thread=False)
                    self.move_to_position(current_position, as_thread=False)
                # pickup failed
                elif try_num >= self.__MAX_PICKUP_TRIES:
                    raise GetProductError(f"{self.name} :Product still at Sensor, grip failed")

                try_num += 1
                
            self.position = current_program_position + 1
        
        except (SensorTimeoutError, ValueError, EncoderOverflowError, GetProductError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)


    def move_to_position(self, position: Position, ignore_moving_pos=False, as_thread=True) -> True:
        '''Moves Robot to given position.

        Args:
            position (Position): to move to (rotation, horizontal, vertical): int.
            ignore_moving_pos (bool): If True robot won't move to moving Position.
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(position, ignore_moving_pos, False), name=self.name)
            self.thread.start()
            return

        
        end_position = position
        self.log.warning(f"{self.name} :Moving to Position: {end_position}")

        # ignore moving position if rotation and one other axis doesn't move
        if position.rotation == -1 and (position.horizontal == -1 or position.vertical == -1):
            ignore_moving_pos = True
        try:
            if not ignore_moving_pos:
                # move to moving position
                self.switch_state(State.TO_MOVING_POS)
                if self.__encoder_ver.get_current_value() <= self.__moving_position.vertical:
                    # if robot is higher than moving postion rotate directly
                    self.__move_all_axes(Position(position.rotation, self.__moving_position.horizontal, self.__moving_position.vertical))
                else:
                    self.__move_all_axes(self.__moving_position)

                # move non moving position axes
                self.switch_state(State.MOVING)
                # only move axis if there was no moving position for axis or the value is smaller than the moving position
                if self.__moving_position.rotation == -1 or position.rotation < self.__moving_position.rotation:
                    rotation = position.rotation
                    position.rotation = -1
                else:
                    rotation = -1
                if self.__moving_position.horizontal == -1 or position.horizontal < self.__moving_position.horizontal:
                    horizontal = position.horizontal
                    position.horizontal = -1
                else:
                    horizontal = -1
                if self.__moving_position.vertical == -1 or position.vertical < self.__moving_position.vertical:
                    vertical = position.vertical
                    position.vertical = -1
                else:
                    vertical = -1
                self.__move_all_axes(Position(rotation, horizontal, vertical))

            # move to destination
            self.switch_state(State.TO_DESTINATION)
            self.__move_all_axes(position)
        
        except (SensorTimeoutError, ValueError, EncoderOverflowError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.log.warning(f"{self.name} :Position reached: {end_position}")
            self.position += 1


    def __move_all_axes(self, position: Position):
        '''Makes linear move to given position, set a axis to -1 to not move that axis.

        Args:
            position (Position): to move to (rotation, horizontal, vertical): int.
        Raises:
            SensorTimeoutError: Timeout is reached (no detection happened).
            ValueError: Counter jumped values.
            EncoderOverflowError: Encoder hat overflow, because value went lower than 0.
        '''
        self.log.info(f"{self.name} :Moving axes to: {position}")

        # get current position
        current_position = Position(
            self.__encoder_rot.get_current_value(),
            self.__encoder_hor.get_current_value(),
            self.__encoder_ver.get_current_value()
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
        self.__motor_rot.move_axis(dir_rot, position.rotation, current_position.rotation, self.__move_threshold_rot, self.__encoder_rot, self.name + "_REF_SW_ROTATION", timeout_in_s=20, as_thread=True)
        self.__motor_hor.move_axis(dir_hor, position.horizontal, current_position.horizontal, self.__MOVE_THRESHOLD_HOR, self.__encoder_hor, self.name + "_REF_SW_HORIZONTAL", as_thread=True)
        self.__motor_ver.move_axis(dir_ver, position.vertical, current_position.vertical, self.__MOVE_THRESHOLD_VER, self.__encoder_ver, self.name + "_REF_SW_VERTICAL", timeout_in_s=15, as_thread=True)

        # wait for end of each move
        self.__motor_rot.join()
        self.__motor_hor.join()
        self.__motor_ver.join()

        self.log.info(f"{self.name} :Axes moved to: {position}")


    def grip(self, as_thread=True):
        '''Grip product. Abstract function, see subclass.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        pass
    def release(self, as_thread=True):
        '''Release product. Abstract function, see subclass.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        pass
    def reset_claw(self, as_thread=True):
        '''Reset gripper. Abstract function, see subclass.
        
        Args:
            as_thread (bool): Runs the function as a thread.
        '''
        pass

class GetProductError(SystemError):
    '''Robot could not grip Product.'''
