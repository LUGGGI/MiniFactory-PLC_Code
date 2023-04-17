'''
parent class for alle machine modules

Author: Lukas Beck
Date: 10.04.2023
'''
from datetime import datetime
from enum import Enum
from logger import log

class State(Enum):
    '''Parent class for all state machines'''
    INIT = 0
    START = 1
        
    END = 20
    ERROR = 30

class Machine:
    '''Parent class for alle machine modules'''

    ready_for_next = False
    waiting_for_transport = False
    error_no_product_found = False


    def __init__(self, time_to_run):
        self.time_to_run = time_to_run
        self.time_start = datetime.now()
        
        log.debug("Created Maschine")

    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of object'''
        run_time = (datetime.now() - self.time_start).total_seconds()
        log.info("Runtime: " + str(run_time))
        run_time = round(run_time)
        return run_time
    
    def get_state_time(self) -> int:
        '''Get run time of state in seconds since switch'''
        state_time = (datetime.now() - self.state_time_start).total_seconds()
        log.info("State time: " + str(state_time))
        state_time = round(state_time)
        return state_time
    
    def switch_state(self, state):
        '''Switch to given state and save state start time'''
        self.state_time_start = datetime.now()
        log.info("Switching state to: " + str(state) + " in " + str(type(self).__name__))
        return state
