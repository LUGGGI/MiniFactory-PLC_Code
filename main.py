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
from sensor import Sensor
from conveyor import Conveyor
from punch_mach import PunchMach
from mp_station import MPStation
from grip_robot import GripRobot, Position, State as State_3D
from vac_robot import VacRobot
from sort_line import SortLine
from warehouse import Warehouse

class Status(Enum):
    NONE = 0
    FREE = 1
    RUNNING = 2
    BLOCKED = 3

class State(Enum):
    INIT = [0, Status.FREE]

    CB1 = [11, Status.FREE]
    CB3_TO_WH = [131, Status.FREE]
    CB3_TO_CB4 = [132, Status.FREE]
    CB4 = [14, Status.FREE]
    CB5 = [15, Status.FREE]

    GR1_CB1_TO_CB3 = [211, Status.FREE]
    GR1_CB1_TO_PM = [212, Status.FREE]
    GR1_PM_TO_CB3 = [213, Status.FREE]
    GR2 = [22, Status.FREE]
    GR3 = [23, Status.FREE]

    VG2 = [32, Status.FREE]

    MPS = [5, Status.FREE]
    PM = [6, Status.FREE]
    SL = [7, Status.FREE]
    WH_STORE = [81, Status.FREE]
    WH_RETRIEVE = [82, Status.FREE]

    WAITING = [99, Status.FREE]
    END = [100, Status.FREE]
    ERROR = [999, Status.FREE]
    TEST = [1000, Status.FREE]

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
    FACTORY = "right"

    def __init__(self, revpi, name: str, config: dict, exit_handler: ExitHandler):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, name)

        self.exit_handler = exit_handler
        self.state = State.INIT
        self.next_state: State = None
        self.previous_state: State = None
        self.machines: "dict[str, Machine]" = {}
        self.config = config
        self.ready_for_transport = "None"

    def run(self):
        '''Starts the mainloop.'''
        self.switch_state(self.config["start_at"])
        log.info(f"{self.name}: Start Mainloop")
        while(not self.error_exception_in_machine and not self.end_machine and not self.exit_handler.was_called):
            try:
                self.mainloop()
                sleep(0.02)
            except Exception as error:
                self.error_exception_in_machine = True
                log.exception(error)
                self.switch_state(State.ERROR)

        self.machines.clear()
        log.critical(f"END of Mainloop: {self.name}")

    def mainloop_config(self):
        '''Config functionality'''
        for machine in self.machines.values():
            # look for errors in the machines
            if machine.error_exception_in_machine:
                self.switch_state(State.ERROR)
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
        for state in State:
            if state.value[1] != Status.FREE:
                machine_name = state.name.split('_')[0]
                machine = self.machines.get(machine_name, None)
                if machine == None and self.ready_for_transport != machine_name:
                    self.switch_status(state, Status.FREE)
        
        if self.state == State.ERROR:
            log.error("Error in Mainloop")
            self.exit_handler.stop_factory()
            self.error_exception_in_machine = True
            return

        if self.state == State.WAITING:
        # wait for running or blocked machines
            if self.next_state.value[1] == Status.FREE:
                self.switch_status(self.previous_state, Status.FREE)
                log.critical(f"{self.name}: Continuing to: {self.next_state}")
                self.switch_state(self.next_state)

        if self.state == State.END:
            State.END.value[1] = Status.FREE
            if not self.end():
                return
            self.end_machine = True
            return
        
    def mainloop(self):
        '''Abstract function should never be called'''
        raise Exception("Abstract function called")

    def switch_state(self, state: State, wait=False):
        '''Switch to given state and save state start time.
        
        :state: state Enum to switch to
        :wait: waits for input bevor switching
        '''
        if self.state == self.config["end_at"]:
            state = State.END
        if state.value[1] == Status.FREE:
            self.switch_status(self.state, Status.FREE)
            self.state = super().switch_state(state, wait=False)

            self.switch_status(self.state, Status.BLOCKED)
            self.state.value[1] = Status.RUNNING
        else:
            log.critical(f"{self.name}: Waiting for: {state}")
            self.switch_status(self.state, Status.BLOCKED)
            self.previous_state = self.state
            self.next_state = state
            self.state = super().switch_state(State.WAITING, wait=False)

    def switch_status(self, state_name, status: Status):
        '''Switch status in states, switches all to a machine belonging states
        
        :state: can be a State Enum or a string of to switching state
        :status: Status that the state should be switched to
        '''
        if type(state_name) == State:
            state_name = state_name.name.split('_')[0]

        for state in State:
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
            

# Start RevPiApp app
if __name__ == "__main__":
    # setup RevpiModIO
    try:
        revpi = RevPiModIO(autorefresh=True)
    except:
        # load simulation if not connected to factory
        revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.img")
    
    revpi.mainloop(blocking=False)
    exit_handler = ExitHandler(revpi)

    configs = [
        {
            "name": "INIT", 
            "start_when": "start",
            "start_at": State.INIT,
            "end_at": State.END,
            "with_oven": False,
            "with_PM": False,
            "with_WH": False,
            "color": "COLOR_UNKNOWN",
            "running": False
        },
        {
            "name": "1_Main", 
            "start_when": "INIT",
            "start_at": State.GR2,
            "end_at": State.WH_STORE,
            "with_oven": False,
            "with_PM": True,
            "with_WH": True,
            "color": "RED",
            "running": False
        },
        {
            "name": "2_Main", 
            "start_when": "INIT",
            "start_at": State.WH_RETRIEVE,
            "end_at": State.END,
            "with_oven": False,
            "with_PM": False,
            "with_WH": True,
            "color": "BLUE",
            "running": False
        },
        {
            "name": "3_Main", 
            "start_when": "INIT",
            "start_at": State.CB1,
            "end_at": State.END,
            "with_oven": False,
            "with_PM": False,
            "with_WH": False,
            "color": "WHITE",
            "running": False
        }
    ]
    
    stage = "start"
    threads: "list[threading.Thread]" = []
    main_loops: "list[MainLoop]" = []

    for config in configs:
        main_loops.append(MainLoop(revpi, config["name"], config, exit_handler))
        threads.append(threading.Thread(target=main_loops[-1].run, name=config["name"]))

    exception = False
    running = True
    while(running and not exception):
        for main_loop in main_loops:
            if main_loop.error_exception_in_machine:
                log.error(f"Error in mainloop {main_loop.name}")
                exception = True
            
        running = False
        for config, thread in zip(configs, threads):
            
            if not config["running"] and config["start_when"] == stage:
                log.critical(f"Start: {config['name']}")
                thread.start()
                config["running"] = True

            if config["running"]:
                running = True
                if not thread.is_alive():
                    config["running"] = False
                    stage = config["name"]
                    log.critical(f"Stop: {config['name']}")
                    break
        
        sleep(1)

    log.critical("End of program")
    revpi.exit()


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
        self.exit_handler = ExitHandler(revpi)
        
        self.stage = "start"
        self.threads: "list[threading.Thread]" = []
        self.main_loops: "list[MainLoop]" = []

    def add_mainloop(self, name: str, mainloop: MainLoop):
        '''Add a new config'''

        self.main_loops.append(mainloop)
        self.threads.append(threading.Thread(target=mainloop.run, name=name))

    def run_factory(self, configs: "list[dict]"):
        '''Runs the factory and starts every mainloop'''
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