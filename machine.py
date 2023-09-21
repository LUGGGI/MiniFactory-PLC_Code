'''Parent class for all machine modules'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.21"

import threading
from datetime import datetime
from time import time

from revpimodio2 import RevPiModIO
from logger import log

class Machine:
    '''Parent class for all machine modules.
    
    Methodes:
        get_run_time(): Get run time of machine
        get_state_time(): Get run time of current state
        switch_state(): Switch to given state
        is_position(): Returns True if no thread is running and given position is current position.
    Attributes:
        revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
        name (str): Exact name of the sensor in PiCtory (everything bevor first '_').
        line_name (str): Name of current line.
        thread (Thread): Thread object if a function is called as thread.
        __time_start (float): Time of machine start.
        __state_time_start (float): Time of current state start.
        end_machine (bool): True if machine should end.
        error_exception_in_machine (bool): True if exception in machine.
        problem_in_machine (bool): True if problem in machine.
        position (int): Counts up the positions of the machine.
        state (State): Current state of machine.
        log (Logger): Log object to print to log.
    '''

    def __init__(self, revpi: RevPiModIO, name: str, line_name: str):
        '''Parent class for all machine modules.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the sensor in PiCtory (everything bevor first '_').
            line_name (str): Name of current line.
        '''
        self.revpi = revpi
        self.name = name
        self.line_name = line_name

        self.__time_start = time()
        self.__state_time_start = time()

        self.thread: threading.Thread = None

        self.end_machine = False
        self.error_exception_in_machine = False
        self.problem_in_machine = False

        self.position = 0
        self.state = None

        global log
        self.log = log.getChild(f"{self.line_name}(Mach)")

    
    def __del__(self):
        self.log.debug(f"Destroyed {type(self).__name__}: {self.name}")


    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of Machine.
        
        Returns:
            int: Run time of machine
        '''
        run_time = round(time() - self.__time_start)
        return run_time


    def get_state_time(self) -> int:
        '''Get run time of state in seconds since switch.
        
        Returns:
            int: Run time of machine
        '''
        state_time = round(time() - self.__state_time_start)
        self.log.info(f"{self.state} time: + {state_time}")
        return state_time


    def switch_state(self, state, wait=False):
        '''Switch to given state and save state start time.
        
        Args:
            state (State): State Enum to switch to.
            wait (bool): Waits for input bevor switching.
        '''
        if wait:
            input(f"Press any key to go to switch: {self.name} to state: {state.name}...\n")
        self.__state_time_start = datetime.now()
        self.state = state

        self.log.warning(self.name + ": Switching state to: " + str(state.name))

    
    def is_position(self, postion: int) -> bool:
        '''Returns True if no thread is running and given position is current position.
        
            position (int): position at which it should return True.
        '''
        try:
            # False, if current thread is active
            if self.thread.is_alive():
                return False
        except AttributeError:
            pass
        # False, if given position is not current position
        if postion != self.position:
            return False

        return True


    def get_status_dict(self) -> dict:
        '''Returns a dictionary with the machine status.
        
        Returns:
            dict: Status dictionary
        '''
        return {
            "state": self.state.name if self.state else None,
            "position": self.position,
            "end_machine": False if not self.end_machine else f"true, Runtime: {self.get_run_time()} s",
            "error_exception_in_machine": self.error_exception_in_machine,
            "problem_in_machine": self.problem_in_machine
        }