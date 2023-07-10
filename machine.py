'''Parent class for all machine modules'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.14"

import threading
from datetime import datetime

from revpimodio2 import RevPiModIO
from logger import log

class Machine:
    '''Parent class for all machine modules.
    
    get_run_time(): Get run time of machine
    get_state_time(): Get run time of state
    switch_state(): Switch to given state
    is_stage(): Returns True if no thread is running and given stage is current stage.
    '''

    def __init__(self, revpi: RevPiModIO, name: str):
        '''Initializes the Maschine
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        self.name = name
        self.revpi = revpi
        self.__time_start = datetime.now()
        self.__state_time_start = datetime.now()

        self.thread: threading.Thread = None

        self.start_next_machine = False
        self.end_machine = False
        self.ready_for_next = False
        self.ready_for_transport = False
        self.error_exception_in_machine = False

        self.stage = 0 # can count up the stages of a machine
        self.state_is_init = False

        self.state = None
        # self.__time_start: datetime = None
        # self.__state_time_start: datetime = None


    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of object.'''
        run_time = (datetime.now() - self.__time_start).total_seconds()
        log.info("Runtime: " + str(run_time))
        run_time = round(run_time)
        return run_time


    def get_state_time(self) -> int:
        '''Get run time of state in seconds since switch.'''
        state_time = (datetime.now() - self.__state_time_start).total_seconds()
        log.info(str(self.state) + " time: " + str(state_time))
        state_time = round(state_time)
        return state_time


    def switch_state(self, state, wait=False):
        '''Switch to given state and save state start time.
        
        :state: state Enum to switch to
        :wait: waits for input bevor switching
        '''
        if wait:
            input(f"Press any key to go to switch: {self.name} to state: {state.name}...\n")
        # self.__state_time_start = datetime.now()
        self.state_is_init = False
        if self.name.lower().find("main") == -1 and self.name.lower().find("init") == -1:
            log.warning(self.name + ": Switching state to: " + str(state.name))
        return state

    
    def is_stage(self, stage: int) -> bool:
        '''Returns True if no thread is running and given stage is current stage.
        
        :stage: stage at which it should return True
        '''
        try:
            # False, if current thread is active
            if self.thread.is_alive():
                return False
        except AttributeError:
            pass
        # False, if given stage is not current stage
        if stage != self.stage:
            return False

        return True
