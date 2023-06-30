'''
Main Loop config for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.30"

from time import sleep
from enum import Enum
import threading
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from logger import log
from machine import Machine

class Status(Enum):
    NONE = 0
    FREE = 1
    RUNNING = 2
    BLOCKED = 3

class MainLoop(Machine):
    '''Controls the MiniFactory.
    
    run(): Starts the mainloop
    mainloop_config(): Config functionality
    mainloop(): Calls the different states
    switch_state(): Switches state to given state if not BLOCKED or RUNNING
    switch_status(): Switch status in states
    end(): Waits for any machines left running.
    run_...(): Calls the different modules
    '''

    def __init__(self, revpi, name: str, config: dict, exit_handler: ExitHandler, states):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, name)

        self.config = config
        self.exit_handler = exit_handler
        self.states = states
        self.next_state = None
        self.previous_state = None
        self.machines: "dict[str, Machine]" = {}
        self.ready_for_transport = "None"

    def run(self):
        '''Starts the mainloop.'''
        self.switch_state(self.config["start_at"], False)
        log.info(f"{self.name}: Start Mainloop")
        while(not self.error_exception_in_machine and not self.end_machine and not self.exit_handler.was_called):
            try:
                self.mainloop()
                sleep(0.02)
            except Exception as error:
                self.error_exception_in_machine = True
                log.exception(error)
                self.switch_state(self.states.ERROR)

        self.machines.clear()
        log.critical(f"END of Mainloop: {self.name}")

    def mainloop_config(self):
        '''Config functionality'''
        for machine in self.machines.values():
            # look for errors in the machines
            if machine.error_exception_in_machine:
                self.switch_state(self.states.ERROR)
                break
            # look for ready_for_transport in machines and sets status to True
            elif machine.ready_for_transport:
                machine.ready_for_transport = False
                log.info(f"{self.name}: Ready for transport: {machine.name}")
                self.ready_for_transport = machine.name
            # end machines 
            elif machine.end_machine and not machine.ready_for_transport:
                log.info(f"{self.name}: Ended: {machine.name}")
                self.machines.pop(machine.name)
                break
        
        # switch Status of State to FREE if machine is done
        for state in self.states:
            if state.value[1] != Status.FREE:
                machine_name = state.name.split('_')[0]
                machine = self.machines.get(machine_name, None)
                if machine == None and self.ready_for_transport != machine_name:
                    self.switch_status(state, Status.FREE)
        
        if self.state == self.states.ERROR:
            log.error("Error in Mainloop")
            self.exit_handler.stop_factory()
            self.error_exception_in_machine = True
            return

        if self.state == self.states.WAITING:
        # wait for running or blocked machines
            if self.next_state.value[1] == Status.FREE:
                self.switch_status(self.previous_state, Status.FREE)
                log.critical(f"{self.name}: Continuing to: {self.next_state}")
                self.switch_state(self.next_state)

        if self.state == self.states.END:
            self.states.END.value[1] = Status.FREE
            if not self.end():
                return
            self.end_machine = True
            return
        
    def mainloop(self):
        '''Abstract function should never be called'''
        raise Exception("Abstract function called")

    def switch_state(self, state, wait=False):
        '''Switch to given state and save state start time.
        
        :state: state Enum to switch to
        :wait: waits for input bevor switching
        '''
        if self.state == self.config["end_at"]:
            state = self.states.END
        if state.value[1] == Status.FREE:
            self.switch_status(self.state, Status.FREE)
            self.state = super().switch_state(state, wait)

            self.switch_status(self.state, Status.BLOCKED)
            self.state.value[1] = Status.RUNNING
        else:
            log.critical(f"{self.name}: Waiting for: {state}")
            self.switch_status(self.state, Status.BLOCKED)
            self.previous_state = self.state
            self.next_state = state
            self.state = super().switch_state(self.states.WAITING, wait=False)

    def switch_status(self, state_name, status: Status):
        '''Switch status in states, switches all to a machine belonging states
        
        :state: can be a State Enum or a string of to switching state
        :status: Status that the state should be switched to
        '''
        if type(state_name) != str:
            state_name = state_name.name.split('_')[0]

        for state in self.states:
            if state.name.split('_')[0].find(state_name) != -1:
                state.value[1] = status

    def is_ready_for_transport(self, machine_name):
        '''Returns true if given machine is ready_for_transport.
        
        :machine_name: Name of machine that should be checked
        '''
        if self.ready_for_transport == machine_name:
            self.ready_for_transport = False
            return True
        else:
            return False
        
    def get_machine(self, machine_name: str, machine_class, *args):
        '''Returns given machine, if not available initializes it.
        
        :machine_name: Name of machine that should be returned
        :machine_class: Class of the machine
        :*args: additional arguments passed to machine
        '''
        machine = self.machines.get(machine_name)
        if machine == None:
            machine = machine_class(self.revpi, machine_name, *args)
            self.machines[machine_name] = machine
        return machine
    
    def end(self) -> False:
        '''Waits for any machines left running.'''
        machine_running = False
        while(True):
            # check if there any machines left running
            machine: Machine
            for machine in self.machines.values():
                if not machine.end_machine and not machine.name == "Main":
                    # wait for running machines
                    machine_running = True
                    if machine.stage != 100:
                        log.info(f"Waiting for machine to end: {machine.name}")
                        machine.stage = 100
            if machine_running:
                return False
            # all machines have ended
            self.end_machine
            return True
            

class Setup():
    '''Setup Mainloop'''
    def __init__(self) -> None:
        '''Init setup and setup RevpiModIO'''
        # setup RevpiModIO
        try:
            self.revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            self.revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.img")
        
        self.revpi.mainloop(blocking=False)
        self.exit_handler = ExitHandler(self.revpi)
        
        self.stage = "start"
        self.threads: "list[threading.Thread]" = []
        self.main_loops: "list[MainLoop]" = []

    def add_mainloop(self, name: str, mainloop: MainLoop):
        '''Add a new config
        
        :name: Name of given mainloop
        :mainloop: Mainloop object to add
        '''

        self.main_loops.append(mainloop)
        self.threads.append(threading.Thread(target=mainloop.run, name=name))

    def run_factory(self, configs: "list[dict]"):
        '''Runs the factory and starts every mainloop
        
        :configs: list of configs, same order as mainloops where added
        '''
        exception = False
        running = True
        while(running and not exception):
            for main_loop in self.main_loops:
                if main_loop.error_exception_in_machine:
                    log.error(f"Error in mainloop {main_loop.name}")
                    exception = True
                
            running = False
            for config, thread in zip(configs, self.threads):
                
                if not config["running"] and config["start_when"] == self.stage:
                    log.critical(f"Start: {config['name']}")
                    thread.start()
                    config["running"] = True

                if config["running"]:
                    running = True
                    if not thread.is_alive():
                        config["running"] = False
                        self.stage = config["name"]
                        log.critical(f"Stop: {config['name']}")
                        break
            
            sleep(1)

        log.critical("End of program")
        self.revpi.exit()