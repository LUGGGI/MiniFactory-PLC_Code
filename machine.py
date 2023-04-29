'''
parent class for alle machine modules

Author: Lukas Beck
Date: 10.04.2023
'''
from datetime import datetime
from logger import log

class Machine:
    '''Parent class for alle machine modules'''

    ready_for_next = False
    ready_for_transport = False
    error_no_product_found = False


    def __init__(self, revpi, name):
        self.rev_pi = revpi
        self.name = name
        self.time_start = datetime.now()
        
        log.debug("Created Maschine for: " + self.name)

    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of object'''
        run_time = (datetime.now() - self.time_start).total_seconds()
        log.info("Runtime: " + str(run_time))
        run_time = round(run_time)
        return run_time
    
    def get_state_time(self) -> int:
        '''Get run time of state in seconds since switch'''
        state_time = (datetime.now() - self.state_time_start).total_seconds()
        log.info(str(self.state) + " time: " + str(state_time))
        state_time = round(state_time)
        return state_time
    
    def switch_state(self, state):
        '''Switch to given state and save state start time'''
        self.state_time_start = datetime.now()
        log.info("Switching state to: " + str(state) + " in " + self.name)
        return state
