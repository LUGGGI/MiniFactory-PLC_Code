'''This module controls the 3D Robots, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading

from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator


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
    
    move_all_axes(): Makes linear move to give position.
    move_axis(): Moves one axis to the given trigger value.
    '''

    def __init__(self, revpi, name: str, moving_position: Position):
        '''Initializes the 3D Robot
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)
        self.moving_position = moving_position
        self.state = None

        self.move_threshold_rot = 40
        self.move_threshold_hor = 40
        self.move_threshold_ver = 40

        # get encoder names
        enc_rot = self.name + "_ROTATION_ENCODER"
        enc_hor = self.name + "_HORIZONTAL_ENCODER"
        enc_ver = self.name + "_VERTICAL_ENCODER"
        if self.name.find("GR") != -1:
            enc_hor = self.name + "_HORIZONTAL_COUNTER"
            self.move_threshold_hor = 2

        # get encoder
        self.encoder_rot = Sensor(self.revpi, enc_rot)
        self.encoder_hor = Sensor(self.revpi, enc_hor)
        self.encoder_ver = Sensor(self.revpi, enc_ver)

        # get motors
        self.motor_rot = Actuator(self.revpi, self.name, "rotation")
        self.motor_hor = Actuator(self.revpi, self.name, "horizontal")
        self.motor_ver = Actuator(self.revpi, self.name, "vertical")

        log.debug("Created 3D Robot: " + self.name)

    def __del__(self):
        log.debug("Destroyed 3D Robot: " + self.name)


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
        
        log.info(f"3D-{self.name} :Moving axes to: {position}")
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

        log.info(f"3D-{self.name} :Moving completed to: {position}")

    # TODO: Move Moving position
  