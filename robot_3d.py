'''
This module controls the 3D Robots, it inherits from machine

Author: Lukas Beck
Date: 01.05.2023
'''
import threading
from enum import Enum
from time import sleep

from logger import log
from machine import Machine
from sensor import Sensor
from motor import Motor

axes = {
    "horizontal": {
        "init_dir": "BWD",
        "ref_sw": "GR1_REF_SW_HORIZONTAL",
        "encoder": "GR1_HORIZONTAL_COUNTER"
    },
    "vertical": {
        "init_dir": "UP",
        "ref_sw": "GR1_REF_SW_VERTICAL",
        "encoder": "GR1_VERTICAL_ENCODER"
    },
    "rotation": {
        "init_dir": "CW",
        "ref_sw": "GR1_REF_SW_ROTATION",
        "encoder": "GR1_ROTATION_ENCODER"
    },
}

'''
cb1: 2150, 180, 50
'''

class State(Enum):
    INIT = 0
    END = 100
    ERROR = 999

class Robot3D(Machine):
    '''Controls the 3D Robot'''

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)
        self.state = None
        log.debug("Created 3D Robot: " + self.name)

    def __del__(self):
        log.debug("Destroyed 3D Robot: " + self.name)

    def init(self, as_tread=False):
        '''Moves the Gripper robot into his init position'''
        # call this function again as a thread
        if as_tread:
            self.thread = threading.Thread(target=self.init, args=(), name=self.name + "_INIT")
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)

        vertical = Motor(self.revpi, self.name, "vertical")
        horizontal = Motor(self.revpi, self.name, "horizontal")
        rotation = Motor(self.revpi, self.name, "rotation")
        claw = Motor(self.revpi, self.name, "claw")

        vertical.run_to_encoder_start("UP", self.name + "_REF_SW_VERTICAL", self.name + "_VERTICAL_ENCODER", as_thread=True)
        horizontal.run_to_encoder_start("BWD", self.name + "_REF_SW_HORIZONTAL", self.name + "_HORIZONTAL_COUNTER", as_thread=True)
        sleep(1)
        rotation.run_to_encoder_start("CW", self.name + "_REF_SW_ROTATION", self.name + "_ROTATION_ENCODER", timeout_in_s=20, as_thread=True)
        claw.run_to_encoder_start("OPEN", self.name + "_REF_SW_CLAW", self.name + "_CLAW_COUNTER", as_thread=True)

        vertical.thread.join()
        horizontal.thread.join()
        rotation.thread.join()
        claw.thread.join()

        log.info("3D Robot in init position")

    def run(self, as_tread=False):
        if as_tread:
            self.thread = threading.Thread(target=self.run, args=(), name=self.name)
            self.thread.start()
            return

        vertical = Motor(self.revpi, self.name, "vertical")
        rotation = Motor(self.revpi, self.name, "rotation")
        horizontal = Motor(self.revpi, self.name, "horizontal")
        claw = Motor(self.revpi, self.name, "claw")

        # move to moving position
        claw.run_to_encoder_value("CLOSE", "GR1_CLAW_COUNTER", 10, as_thread=True)
        vertical.run_to_encoder_value("DOWN", "GR1_VERTICAL_ENCODER", 1400, as_thread=True)

        

        # move to cb1
        rotation.run_to_encoder_value("CCW", "GR1_ROTATION_ENCODER", 190, as_thread=True)
        horizontal.run_to_encoder_value("FWD", "GR1_HORIZONTAL_COUNTER", 60, as_thread=True)
        rotation.thread.join()
        vertical.thread.join()

        # grip product
        vertical.run_to_encoder_value("DOWN", "GR1_VERTICAL_ENCODER", 2050, as_thread=False)
        claw.run_to_encoder_value("CLOSE", "GR1_CLAW_COUNTER", 15, as_thread=False)
        vertical.run_to_encoder_value("UP", "GR1_VERTICAL_ENCODER", 1400, as_thread=False)

        # move to cb3
        # rotation.run_to_encoder_value("CCW", "GR1_ROTATION_ENCODER", 2380, as_thread=True)
        # horizontal.run_to_encoder_value("BWD", "GR1_HORIZONTAL_COUNTER", 0, as_thread=True)
        # rotation.thread.join()

        # move to cb2
        rotation.run_to_encoder_value("CCW", "GR1_ROTATION_ENCODER", 3832, as_thread=True)
        horizontal.run_to_encoder_value("FWD", "GR1_HORIZONTAL_COUNTER", 80, as_thread=True)
        rotation.thread.join()
        vertical.thread.join()

        # release product
        vertical.run_to_encoder_value("DOWN", "GR1_VERTICAL_ENCODER", 2050, as_thread=False)
        claw.run_to_encoder_value("OPEN", "GR1_CLAW_COUNTER", 10, as_thread=True)
        vertical.run_to_encoder_value("UP", "GR1_VERTICAL_ENCODER", 1500, as_thread=False)
        

        log.info("3D Robot in endposition")
        self.ready_for_transport = True
        return

        