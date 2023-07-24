'''
Main Loop config for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.24"

from time import sleep
from enum import Enum
import threading
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from logger import log
from machine import Machine
from state_logger import StateLogger

class Status(Enum):
    NONE = 0
    FREE = 1
    RUNNING = 2
    BLOCKED = 3
    WAITING = 4

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

    def __init__(self, revpi, name: str, config: dict, states):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, name, name)

        global log
        self.log = log.getChild(f"{self.mainloop_name}(Set)")

        self.config = config
        self.states = states
        self.machines: "dict[str, Machine]" = {}
        self.ready_for_transport = "None"
        self.product_at: str = None
        self.waiting_for_state = None

        self.state_logger = StateLogger()

    def run(self):
        '''Starts the mainloop.'''
        self.switch_state(self.config["start_at"], False)
        self.log.info(f"{self.name}: Start Mainloop")
        while(not self.error_exception_in_machine and not self.end_machine):
            try:
                self.mainloop()
                sleep(0.02)
            except Exception as error:
                self.error_exception_in_machine = True
                self.log.exception(error)
                self.switch_state(self.states.ERROR)

        self.machines.clear()
        self.log.critical(f"END of Mainloop: {self.name}")

    def mainloop_config(self):
        '''Config functionality'''
        for machine in self.machines.values():
            # update status
            self.state_logger.update_machine(self.mainloop_name, machine.name, machine.get_status_dict())
            # look for errors in the machines
            if machine.error_exception_in_machine:
                self.switch_state(self.states.ERROR)
                break
            # look for ready_for_transport in machines and sets status to True
            if machine.ready_for_transport:
                machine.ready_for_transport = False
                self.log.info(f"Ready for transport: {machine.name}")
                self.ready_for_transport = machine.name
            # end machines 
            if machine.end_machine and not machine.ready_for_transport and machine.name != self.product_at:
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

        if self.state == self.states.ERROR:
            self.error_exception_in_machine = True
            return

        if self.state == self.states.END:
            self.states.END.value[1] = Status.FREE
            if not self.end():
                return
            self.end_machine = True
            return
        
        # update mainloop status for state_logger
        status_dict = {
            "state": self.state.name if self.state else None,
            "product_at": self.product_at,
            "ready_for_transport": self.ready_for_transport,
            "waiting_for_state": self.waiting_for_state.name if self.waiting_for_state else None
        }
        self.state_logger.update_machine(self.name, "self", status_dict)

        
    def mainloop(self):
        '''Abstract function should never be called'''
        raise Exception("Abstract function called")

    def switch_state(self, state, wait=False):
        '''Switch to given state and save state start time.
        
        :state: state Enum to switch to
        :wait: waits for input bevor switching
        '''
        if self.state == self.config["end_at"]:
            self.switch_state(self.states.END, wait)
        elif state.value[1] == Status.FREE or state.value[2] == self.name:
            if wait:
                input(f"Press any key to go to switch: {self.name} to state: {state.name}...\n")
            self.log.critical(self.name + ": Switching state to: " + str(state.name))
            self.state = state
        else:
            self.log.critical(f"{self.name}: Waiting for: {state}")
            self.switch_status(self.state, Status.WAITING)
            self.waiting_for_state = state

    def switch_status(self, state_name, status: Status):
        '''Switch status in states, if name switches all to a machine belonging states
        
        :state: can be a State Enum or a string of to switching state
        :status: Status that the state should be switched to
        '''
        # get the used_by tag
        name_tag = "None" if status == Status.FREE else self.name

        if type(state_name) != str:
            state_name.value[1] = status
            # set the used_by tag
            state_name.value[2] = name_tag
        else:
            for state in self.states:
                if state.name.split('_')[0].find(state_name) != -1:
                    # set status
                    state.value[1] = status
                    # set the used_by tag
                    state.value[2] = name_tag
        self.state_logger.update_main_states(self.states)
        self.state_logger.update_file()

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
            machine = machine_class(self.revpi, machine_name, self.name, *args)
            self.machines[machine_name] = machine
            self.switch_status(machine_name, Status.RUNNING)
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
                        self.log.info(f"Waiting for machine to end: {machine.name}")
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
        
        self.stage = None
        self.threads: "list[threading.Thread]" = []
        self.main_loops: "list[MainLoop]" = []
        self.state_logger = StateLogger()

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

        # init state_logger
        names_of_mainsloops = []
        for main_loop in self.main_loops:
            names_of_mainsloops.append(main_loop.name)
        self.state_logger.init("states.json", names_of_mainsloops)


        exception = False
        running = True
        while(running and not exception):
            for main_loop in self.main_loops:
                if main_loop.error_exception_in_machine:
                    log.error(f"Error in mainloop {main_loop.name}")
                    self.exit_handler.stop_factory()
                    exception = True
                    break

            if self.exit_handler.was_called or exception:
                for main_loop in self.main_loops:
                    log.critical(f"Ending mainloop: {main_loop.name}")
                    main_loop.end_machine = True
                return

            running = False
            for config, thread in zip(configs, self.threads):
                if config["finished"]:
                    continue
                if not config["running"] and (config["start_when"] == self.stage or config["start_when"] == "now"):
                    log.critical(f"Start: {config['name']}")
                    thread.start()
                    config["running"] = True

                if config["running"]:
                    running = True
                    if not thread.is_alive():
                        config["running"] = False
                        config["finished"] = True
                        self.stage = config["name"]
                        log.critical(f"Stop: {config['name']}")
                        break
            
            self.state_logger.update_file()
            sleep(0.01)
