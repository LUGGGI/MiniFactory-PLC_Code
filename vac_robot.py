'''This module controls the Vacuum Robot, it inherits from Robot3D'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.08.30"

import threading
from time import sleep

from logger import log
from actuator import Actuator
from robot_3d import Robot3D, Position, State


class VacRobot(Robot3D):
    '''Controls the Vacuum Robot
    
    init(): Move to init position
    grip(): Grip Product
    release(): Release product.
    '''

    def __init__(self, revpi, name: str, mainloop_name: str, moving_position=Position(-1, -1, 1400)):
        '''Initializes the Vacuum Robot.
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :mainloop_name: name of current mainloop
        :moving_position: Positions that the axes should be to allow save moving
        '''
        super().__init__(revpi, name, mainloop_name, moving_position)

        global log
        self.log = log.getChild(f"{self.mainloop_name}(Vac)")

        self.compressor = Actuator(self.revpi, self.name + "_COMPRESSOR", self.mainloop_name)
        self.valve = Actuator(self.revpi, self.name + "_VALVE_VACUUM", self.mainloop_name)

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
            self.log.info(f"{self.name} :Gripping")
            self.compressor.run_for_time("", 0.3, as_thread=True)
            sleep(0.2)
            self.valve.start()
            self.compressor.join()
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
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
            self.log.info(f"{self.name} :Releasing")
            self.valve.stop()
        except Exception as error:
            self.error_exception_in_machine = True
            self.switch_state(State.ERROR)
            self.log.exception(error)
        else:
            self.stage += 1
