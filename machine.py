'''
parent class for alle machine modules

Author: Lukas Beck
Date: 10.04.2023
'''
from datetime import datetime
import time

class Machine:
    '''Parent class for alle machine modules'''

    ready_for_next = False
    waiting_for_transport = False
    error_no_product_found = False

    def __init__(self, time_to_run):
        self.time_to_run = time_to_run
        self.time_start = datetime.now()
        
        print("Created Maschine at " + str(self.time_start))

    def get_run_time(self) -> int:
        '''Get run time of machine in seconds since creation of object'''
        run_time = (datetime.now() - self.time_start).total_seconds()
        print("Runtime: " + str(run_time))
        run_time = round(run_time)
        return run_time