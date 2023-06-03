'''This module controls the Vacuum Robot, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.05.23"

import threading

from logger import log
from actuator import Actuator
from robot_3d import Robot3D, Position, State


class VacRobot(Robot3D):
    '''Controls the Vacuum Robot
    
    init(): Move to init position
    grip(): Grip Product
    release(): Release product.
    '''

    def __init__(self, revpi, name: str, moving_position=Position(-1, -1, 1400)):
        '''Initializes the Vacuum Robot.
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :moving_position: Positions that the axes should be to allow save moving
        '''
        super().__init__(revpi, name, moving_position)

        self.compressor = Actuator(self.revpi, self.name + "_COMPRESSOR")
        self.valve = Actuator(self.revpi, self.name + "_VALVE_VACUUM")

        log.debug("Created Vacuum Robot: " + self.name)


    def __del__(self):
        log.debug("Destroyed Vacuum Robot: " + self.name)
            
    def grip(self, as_thread=False):
        '''Grip Product.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.grip, args=(), name=self.name)
            self.thread.start()
            return
            
        try:
            self.compressor.run_for_time("", 1, as_thread=True)
            self.valve.start()
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1

    def release(self, as_thread=False):
        '''Release product.
        
        :as_thread: Runs the function as a thread
        '''
        if as_thread:
            self.thread = threading.Thread(target=self.release, args=(), name=self.name)
            self.thread.start()
            return
        
        try:
            self.valve.stop()
        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1
