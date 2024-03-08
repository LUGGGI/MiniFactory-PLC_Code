'''
Parent Class for production lines on MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.19"

from enum import Enum

from lib.logger import log
from lib.machine import Machine, MainState

class Status(Enum):
    NONE = 0
    FREE = 1
    RUNNING = 2
    BLOCKED = 3
    WAITING = 4
    PROBLEM = 888
    ERROR = 999

class MainLine(Machine):
    '''Controls the MiniFactory.'''
    '''
    Methodes:
        update(): Updates the line
        line_config(): Config functionality
        mainloop(): Calls the different states
        state_is_free(): Check if given state is FREE or used by current line.
        is_end_state: Check if current state is the end state of current line.
        switch_state(): Switches state to given state if not BLOCKED or RUNNING
        switch_status(): Switch status in states
        end(): Waits for any machines left running.
    Attributes:
        config (dict): Config for the line.
        states (State): States from Subclass.
        machines (dict): All active machines.
        product_at (bool): Name of machine where product is at. 
        waiting_for_state (State): If line is waiting for machine, holds the state of that machine.
        running (bool): True if line is currently running.
        status_dict (dict): Status of line.
    '''

    def __init__(self, revpi, config: dict, states):
        '''Initializes MiniFactory control loop.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            config (dict): Config for the line.
            states (State): States from Subclass.
        '''
        super().__init__(revpi, config["name"], config["name"])

        self.config = config
        self.states = states

        self.machines: "dict[str, Machine]" = {}
        self.product_at: str = None
        self.waiting_for_state = None
        self.running = False
        self.end_line = False

        global log
        self.log = log.getChild(f"{self.line_name}")


    def update(self, run: bool):
        '''Updates the line.
        
        Args:
            run: Only run the line if True.
        '''
        try:
            if self.line_config() and run:
                self.mainloop()
        except Exception as error:
            self.error_handler(error)


    def line_config(self) -> bool:
        '''Config functionality.
        
        Returns:
            bool: False if error occurred else returns True.
        '''
        for machine in self.machines.values():
            # look for errors in the machines
            if machine.state == MainState.ERROR and not self.state == MainState.ERROR:
                self.exception_msg = machine.exception_msg
                self.switch_state(MainState.ERROR)
                self.switch_status(machine.name, Status.ERROR)
                return False
            if machine.state == MainState.PROBLEM and not self.state == MainState.PROBLEM:
                self.exception_msg = machine.exception_msg
                self.switch_state(MainState.PROBLEM)
                self.switch_status(machine.name, Status.PROBLEM)
                return False
            
            # end machines 
            if machine.state == MainState.END and not machine.name == self.product_at:
                self.log.info(f"Ended: {machine.name}")
                self.switch_status(machine.name, Status.FREE)
                self.machines.pop(machine.name)
                break        
        
        if self.waiting_for_state != None:
        # waiting for running or blocked machines
            if self.waiting_for_state.value[1] == Status.FREE:
                self.log.critical(f"Continuing to: {self.waiting_for_state}")
                self.switch_state(self.waiting_for_state)
                self.waiting_for_state = None

        if self.config["run"] == False:
            tmp_end_line = True
            for machine in self.machines.values():
                if self.thread and self.thread.is_alive():
                    tmp_end_line = False
            self.end_line = tmp_end_line

        if self.state == MainState.END:
            self.end()

        if self.state == MainState.ERROR or self.state == MainState.PROBLEM:
            if self.state == MainState.PROBLEM:
                for machine in self.machines.values():
                    if self.thread and self.thread.is_alive():
                        return False
            self.end_line = True
            for state in self.states:
                if state.value[2] == self.name:
                    self.switch_status(state, Status.FREE)

            return False
        # no error occurred
        return True

        
    def mainloop(self):
        '''Abstract function should never be called'''
        raise Exception("Abstract function called")
    

    def state_is_free(self, state):
        '''Check if given state is FREE or used by current line.
        
        Args:
            state (State): State Enum to check.
        Returns:
            bool: True if given state is FREE or used by current line, else False.
        '''
        if isinstance(state, MainState):
            return True
        if state.value[1] == Status.FREE or state.value[2] == self.name:
            return True
        else:
            return False
        
    
    def is_end_state(self):
        '''Check if current state is the end state of current line.
        
        Returns:
            bool: True if current state is end state, else False.
        '''
        if isinstance(self.state, MainState):
            return True
        if self.state == self.config["end_at"]:
            return True
        else:
            return False


    def switch_state(self, state, wait=False):
        '''Switch to given state and save state start time.
        
        Args:
            state (State): State Enum to switch to.
            wait (bool): Calls for input before switching.
        '''
        if self.state == self.config["end_at"] and not isinstance(state, MainState):
            self.switch_status(self.state, Status.FREE)
            self.switch_state(MainState.END, wait)
        elif self.state_is_free(state):
            if wait:
                input(f"Press any key to go to switch: {self.name} to state: {state.name}...\n")
            self.log.critical(self.name + ": Switching state to: " + str(state.name))
            self.state = state
            if not isinstance(state, MainState) or state != self.states.WAITING:
                self.switch_status(state, Status.RUNNING)
        else:
            self.log.critical(f"{self.name}: Waiting for: {state}")
            self.switch_status(self.state, Status.WAITING)
            self.waiting_for_state = state


    def switch_status(self, state_name, status: Status):
        '''Switch status in states, if name switches all to a machine belonging states.
        
        Args:
            state (State | str): Can be a State Enum or a string of to switching state.
            status (Status): Status that the state should be switched to.
        '''
        if isinstance(state_name, MainState):
            return
        # get the used_by tag
        name_tag = "None" if status == Status.FREE else self.name

        if type(state_name) != str:
            state_name = state_name.name
        
        for state in self.states:
            if state.name == state_name:
                # set status
                state.value[1] = status
                # set the used_by tag
                state.value[2] = name_tag
                self.log.debug(f"{self.name}: Switching status of: {state_name} to [{status}, {name_tag}]")
            elif state.name.split('_')[0] == state_name.split('_')[0]:
                # set status
                state.value[1] = Status.FREE if status == Status.FREE else Status.BLOCKED
                # set the used_by tag
                state.value[2] = name_tag
                self.log.debug(f"{self.name}: Switching status of other: {state.name} to [{Status.FREE if status == Status.FREE else Status.BLOCKED}, {name_tag}]")


    def get_machine(self, machine_name: str, machine_class, *args) -> Machine:
        '''Returns given machine, if not available initializes it.
        
        Args:
            machine_name (str): Name of machine that should be returned.
            machine_class (Mainloop): Class of the machine.
            *args: additional arguments passed to machine.
        Returns:
            Machine: machine object for given machine.
        '''
        machine = self.machines.get(machine_name)
        if machine == None:
            machine = machine_class(self.revpi, machine_name, self.name, *args)
            self.machines[machine_name] = machine
            if self.state.name.split('_')[0] != machine_name:
                self.switch_status(machine_name, Status.RUNNING)
        return machine
    
    
    def end(self) -> False:
        '''Waits for any machines left running.
        
        Returns:
            bool: True if all machine have ended else False.
        '''
        machine_running = False
        while(True):
            # check if there any machines left running
            machine: Machine
            for machine in self.machines.values():
                if machine.state != MainState.END and not machine.name == "Main":
                    # wait for running machines
                    machine_running = True
                    if machine.position != 100:
                        self.log.info(f"Waiting for machine to end: {machine.name}")
                        machine.position = 100
            if machine_running:
                return False
            # all machines have ended
            self.end_line = True
            return True
