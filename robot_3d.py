'''
This module controls the 3D Robots, it inherits from machine

Author: Lukas Beck
Date: 18.05.2023
'''
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
        return f"({self.rotation}, {self.horizontal},  {self.vertical})"  

class Robot3D(Machine):
    '''Controls the 3D Robot
    
    move_all_axes(): Makes linear move to give position.
    move_axis(): Moves one axis to the given trigger value.
    '''

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)

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
        
        log.info("Moving axes to position: " + str(position))
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
        if position.rotation < current_position.rotation:
            dir_rot = "CW"
        if position.horizontal < current_position.horizontal:
            dir_hor = "BWD"
        if position.vertical < current_position.vertical:
            dir_ver = "UP"

        
        # move to position
        self.move_axis(self.motor_rot, position.rotation, current_position.rotation, self.move_threshold_rot, dir_rot, self.encoder_rot, self.name + "_REF_SW_ROTATION", timeout_in_s=20, as_thread=True)
        self.move_axis(self.motor_hor, position.horizontal, current_position.horizontal, self.move_threshold_hor, dir_hor, self.encoder_hor, self.name + "_REF_SW_HORIZONTAL", as_thread=True)
        self.move_axis(self.motor_ver, position.vertical, current_position.vertical, self.move_threshold_ver, dir_ver, self.encoder_ver, self.name + "_REF_SW_VERTICAL", as_thread=True)

        # wait for end of each move
        if self.motor_rot.thread.is_alive():
            self.motor_rot.thread.join()
        if self.motor_hor.thread.is_alive():
            self.motor_hor.thread.join()
        if self.motor_ver.thread.is_alive():
            self.motor_ver.thread.join()

        log.info("Move complete to: " + str(position))

        
    def move_axis(self, motor: Actuator, trigger_value: int, current_value: int, move_threshold: int, direction: str, encoder: Sensor, ref_sw: str, timeout_in_s=10, as_thread=False):
        '''Moves one axis to the given trigger value.
        
        :motor: Motor object 
        :trigger_value: Encoder-Value at which the motor stops
        :current_value: Current Encoder-Value to determine if move is necessary
        :move_threshold: Value that has at min to be traveled to start the motor
        :direction: Motor direction, (everything after {NAME}_)
        :encoder: Sensor object
        :ref_sw: Reference Switch at which the motor stops if it runs to the encoder start 
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread

        -> Panics if timeout is reached (no detection happened)
        '''
        # if trigger_value (position) is -1 do not move that axis
        if trigger_value == -1:
            return
        # if trigger value is 0 move to init position
        if trigger_value == 0:
            motor.run_to_encoder_start(direction, ref_sw, encoder, timeout_in_s, as_thread)
        # if trigger value is the same as the current value don't move
        elif abs(current_value - trigger_value) < move_threshold:
            log.info("Axis already at value: " + self.name + motor.type)
        # move to value
        else:
            motor.run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s, as_thread)
  