'''This module controls the 3D Robots, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.29"

import threading
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator

class State(Enum):
    INIT = 0
    TO_MOVING_POS = 1
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
        return f"(r:{self.rotation if self.rotation != -1 else '-'}, h:{self.horizontal if self.horizontal != -1 else '-'}, v:{self.vertical if self.vertical != -1 else '-'})"  

class Robot3D(Machine):
    '''Controls the 3D Robot.
    
    init(): Move to init position.
    move_to_position(): Moves to given position.
    move_all_axes(): Makes linear move to give position.
    '''
    __MOVE_THRESHOLD_ROT = 40
    __MOVE_THRESHOLD_HOR = 40
    __MOVE_THRESHOLD_VER = 40

    def __init__(self, revpi, name: str, moving_position: Position):
        '''Initializes the 3D Robot
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.__moving_position = moving_position

        # get encoder
        self.__encoder_rot = Sensor(self.revpi, self.name + "_ROTATION_ENCODER")
        self.__encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_ENCODER")
        self.__encoder_ver = Sensor(self.revpi, self.name + "_VERTICAL_ENCODER")

        # get pwm pins
        pwm_rot = self.name + "_ROTATION_PWM"
        pwm_hor = self.name + "_HORIZONTAL_PWM" if self.name.find("VG") != -1 else None
        pwm_ver = None

        # get motors
        self.__motor_rot = Actuator(self.revpi, self.name, pwm=pwm_rot, type="rotation")
        self.__motor_hor = Actuator(self.revpi, self.name, pwm=pwm_hor, type="horizontal")
        self.__motor_ver = Actuator(self.revpi, self.name, pwm=pwm_ver, type="vertical")

        log.debug("Created 3D Robot: " + self.name)


    def __del__(self):
        log.debug("Destroyed 3D Robot: " + self.name)


    def init(self, to_end=False, as_thread=True):
        '''Move to init position.
        
        :to_end: set end_machine to True after completion of init
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(to_end, False), name=self.name + "_INIT")
            self.thread.start()
            return

        self.state = self.switch_state(State.INIT)
        try:
            # move to init position
            self.move_all_axes(Position(-1,0,0))
            self.move_all_axes(Position(0,-1,-1))

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            if to_end:
                self.state = self.switch_state(State.END)
                self.end_machine = True
            else:
                log.warning(f"{self.name}: Initialized")
                self.stage += 1


    def grip_and_move_to_position(self, position: Position, sensor: str=None, as_thread=True):
        '''Moves product from current postion to given position.

        :position: (rotation, horizontal, vertical): int
        :sensor: Sensor that will be checked for detection while moving to moving position
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.grip_and_move_to_position, args=(position, sensor, False), name=self.name)
            self.thread.start()
            return

        current_stage = self.stage
        # get current position
        current_position = Position(
            self.__encoder_rot.get_current_value(),
            self.__encoder_hor.get_current_value(),
            self.__encoder_ver.get_current_value()
        )
        self.grip(as_thread = False)

        if self.move_to_position(position, sensor, as_thread=False) == False:
            # move back and try again
            if self.name.find("GR") != -1:
                self.reset_claw(as_thread=False)
            else:
                self.release(as_thread = False)
            self.move_to_position(current_position, as_thread=False)
            self.grip(as_thread = False)
            if self.move_to_position(position, sensor, as_thread=False) == False:
                self.state = self.switch_state(State.ERROR)
                self.error_exception_in_machine = True
                return
        
        self.stage = current_stage + 1


    def move_to_position(self, position: Position, sensor: str=None, ignore_moving_pos=False, as_thread=True) -> True:
        '''Moves to Robot given position.

        :position: (rotation, horizontal, vertical): int
        :sensor: Sensor that will be checked for detection when at moving position
        :ignore_moving_pos: Robot won't move to moving Position
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(position, sensor, ignore_moving_pos, False), name=self.name)
            self.thread.start()
            return

        log.warning(f"{self.name} :Moving to Position: {position}")

        # ignore moving position if rotation and one other axis doesn't move
        if position.rotation == -1 and (position.horizontal == -1 or position.vertical == -1):
            ignore_moving_pos = True
        try:
            if not ignore_moving_pos:
                # move to moving position
                self.state = self.switch_state(State.TO_MOVING_POS)
                if self.__encoder_ver.get_current_value() <= self.__moving_position.vertical:
                    # if robot is higher than moving postion rotate directly
                    self.move_all_axes(Position(position.rotation, self.__moving_position.horizontal, self.__moving_position.vertical))
                else:
                    self.move_all_axes(self.__moving_position)

                # check if Product was picked up
                if sensor and Sensor(self.revpi, sensor).get_current_value() == True:
                    log.error(f"{self.name} :Product still at Sensor")
                    return False
                else:
                    self.ready_for_next = True

                # move non moving position axes
                self.state = self.switch_state(State.MOVING)
                # only move axis if there was no moving position for axis
                rotation = position.rotation if self.__moving_position.rotation == -1 or position.rotation < self.__moving_position.rotation else -1
                horizontal = position.horizontal if self.__moving_position.horizontal == -1 or position.horizontal < self.__moving_position.horizontal else -1
                vertical = position.vertical if self.__moving_position.vertical == -1 or position.vertical < self.__moving_position.vertical else -1
                self.move_all_axes(Position(rotation, horizontal, vertical))

            # move to destination
            self.state = self.switch_state(State.TO_DESTINATION)
            self.move_all_axes(position)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.warning(f"{self.name} :Position reached: {position}")
            self.stage += 1


    def move_all_axes(self, position: Position):
        '''Makes linear move to given position, set a axis to -1 to not move that axis.

        :position: (rotation, horizontal, vertical): int

        -> Panics if axes movements did not complete
        '''
        log.info(f"{self.name} :Moving axes to: {position}")

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
        self.__motor_rot.move_axis(dir_rot, position.rotation, current_position.rotation, self.__MOVE_THRESHOLD_ROT, self.__encoder_rot, self.name + "_REF_SW_ROTATION", timeout_in_s=20, as_thread=True)
        self.__motor_hor.move_axis(dir_hor, position.horizontal, current_position.horizontal, self.__MOVE_THRESHOLD_HOR, self.__encoder_hor, self.name + "_REF_SW_HORIZONTAL", as_thread=True)
        self.__motor_ver.move_axis(dir_ver, position.vertical, current_position.vertical, self.__MOVE_THRESHOLD_VER, self.__encoder_ver, self.name + "_REF_SW_VERTICAL", as_thread=True)

        # wait for end of each move
        self.__motor_rot.join()
        self.__motor_hor.join()
        self.__motor_ver.join()

        log.info(f"{self.name} :Axes moved to: {position}")


    def grip():
        '''Abstract function, see subclass'''
        pass
    def release():
        '''Abstract function, see subclass'''
        pass