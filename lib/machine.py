'''Parent class for all machine modules'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.19"

import threading
from datetime import datetime
from time import time, sleep
from enum import Enum
from revpimodio2 import RevPiModIO

from lib.logger import log

class MainState(Enum):
    '''Main State enum'''
    INIT = 0
    END = 100
    WARNING = 777
    PROBLEM = 888
    ERROR = 999


class Machine:
    '''Parent class for all machine modules.'''
    '''
    Methodes:
        get_run_time(): Get run time of machine.
        get_state_time(): Get run time of current state.
        switch_state(): Switch to given state.
        is_position(): Returns True if no thread is running and given position is current position.
    Attributes:
        revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
        name (str): Exact name of the sensor in PiCtory (everything before first '_').
        line_name (str): Name of current line.
        thread (Thread): Thread object if a function is called as thread.
        __time_start (float): Time of machine start.
        __state_time_start (float): Time of current state start.
        end_machine (bool): True if machine should end.
        position (int): Counts up the positions of the machine.
        state (State): Current state of machine.
        log (Logger): Log object to print to log.
    '''

    def __init__(self, revpi: RevPiModIO, name: str, line_name: str):
        '''Parent class for all machine modules.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the sensor in PiCtory (everything before first '_').
            line_name (str): Name of current line.
        '''
        self.revpi = revpi
        self.name = name
        self.line_name = line_name

        self.__time_start = time()
        self.__state_time_start = time()

        self.thread: threading.Thread = None

        self.exception_msg: str = None

        self.position = 0
        self.state = None

        global log
        self.log = log.getChild(f"{self.line_name}(Mach)")

    
    def __del__(self):
        self.log.debug(f"Destroyed {type(self).__name__}: {self.name}")


    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of Machine.
        
        Returns:
            int: Run time of machine.
        '''
        run_time = round(time() - self.__time_start)
        return run_time


    def get_state_time(self) -> int:
        '''Get run time of state in seconds since switch.
        
        Returns:
            int: Run time of state.
        '''
        state_time = round(time() - self.__state_time_start)
        self.log.info(f"{self.state} time: + {state_time}")
        return state_time


    def switch_state(self, state, wait=False):
        '''Switch to given state and save state start time.
        
        Args:
            state (State): State Enum to switch to.
            wait (bool): Waits for input before switching.
        '''
        if wait:
            input(f"Press any key to go to switch: {self.name} to state: {state.name}...\n")
        self.__state_time_start = datetime.now()
        self.state = state

        self.log.warning(self.name + ": Switching state to: " + str(state.name))

    
    def is_position(self, position: int) -> bool:
        '''Returns True if no thread is running and given position is current position.
        
        Args:
            position (int): position at which it should return True.
        Returns:
            bool: True if no thread is running and at position.
        '''
        try:
            # False, if current thread is active
            if self.thread.is_alive():
                return False
        except AttributeError:
            pass
        # False, if given position is not current position
        if position != self.position:
            return False

        return True
    
    def warning_handler(self, warning_msg):
        '''Handler for warnings.
        
        Args:
            problem_msg: message that is thrown by the machine.
        '''
        self.exception_msg = warning_msg
        self.switch_state(MainState.WARNING)
        self.log.error(f"WARNING: {self.exception_msg}")
        sleep(0.1)

    def problem_handler(self, problem_msg):
        '''Handler for problems.
        
        Args:
            problem_msg: message that is thrown by the machine.
        '''
        self.exception_msg = problem_msg
        self.switch_state(MainState.PROBLEM)
        if self.name.find("_") != -1 and self.thread == None:
            # If called in another machine
            raise
        self.log.exception(f"PROBLEM: {self.exception_msg}")

    def error_handler(self, error_msg):
        '''Handler for errors.
        
        Args:
            error_msg: message that is thrown by the machine.
        '''
        self.exception_msg = error_msg
        self.switch_state(MainState.ERROR)
        if self.name.find("_") != -1 and self.thread == None:
            # If called in another machine
            raise
        self.log.exception(f"ERROR: {self.exception_msg}")
