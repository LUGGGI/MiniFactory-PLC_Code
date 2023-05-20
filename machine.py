'''
parent class for alle machine modules

Author: Lukas Beck
Date: 10.04.2023
'''
from datetime import datetime

from revpimodio2 import RevPiModIO
from logger import log

class Machine:
    '''Parent class for alle machine modules'''
    thread = None

    stage = 0 # can count up the stages of a machine
    ready_for_next = False
    ready_for_transport = False
    error_exception_in_machine = False

    state_is_init = False


    def __init__(self, revpi: RevPiModIO, name: str):
        self.name = name
        self.revpi = revpi
        self.__time_start = datetime.now()
        self.__state_time_start = datetime.now()
        
        log.debug("Created Maschine for: " + self.name)

    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of object'''
        run_time = (datetime.now() - self.__time_start).total_seconds()
        log.info("Runtime: " + str(run_time))
        run_time = round(run_time)
        return run_time
    
    def get_state_time(self) -> int:
        '''Get run time of state in seconds since switch'''
        state_time = (datetime.now() - self.__state_time_start).total_seconds()
        log.info(str(self.state) + " time: " + str(state_time))
        state_time = round(state_time)
        return state_time
    
    def switch_state(self, state):
        '''Switch to given state and save state start time'''
        self.__state_time_start = datetime.now()
        self.state_is_init = False
        log.warning(self.name + ": Switching state to: " + str(state))
        return state
