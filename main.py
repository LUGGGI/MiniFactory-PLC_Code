'''
Main Loop for MiniFactory project for machines:
Conveyor
PunchMach
Warehouse
VacRobot
GripRobot
SortLine
MPStation
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.26"

from time import sleep
from enum import Enum
import threading
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from logger import log
from machine import Machine
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
    CB2 = [12, Status.FREE]
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
    
    run(): starts the mainloop
    mainloop(): calls the different states
    switch_state(): switches state to given state if not BLOCKED or RUNNING
    run_...(): calls the different modules
    end(): Waits for any machines left running.
    '''
    FACTORY = "right"

    def __init__(self, revpi, name: str, config: dict, exit_handler: ExitHandler):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, name)

        self.exit_handler = exit_handler
        self.state = State.INIT
        self.next_state: State = None
        self.previous_state: State = None
        self.machines = {}
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
      
    def mainloop(self):
        machine: Machine
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
                self.switch_status(machine.name, Status.FREE)
                break
        
        if self.state == State.ERROR:
            log.error("Error in Mainloop")
            self.exit_handler.stop_factory()
            self.error_exception_in_machine = True
            return

        # wait for running or blocked machines
        if self.state == State.WAITING:
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

        if self.state == State.TEST:
            if self.test():
                return
            
        if self.state == State.INIT:
            if self.run_init():
                self.switch_state(State.END)

        elif self.state == State.GR2:
            if self.run_gr2():
                self.switch_state(State.MPS)

        elif self.state == State.MPS:
            if self.run_mps():
                self.switch_state(State.CB1)

        elif self.state == State.CB1:
            if self.run_cb1():
                if self.config["with_PM"]:
                    self.switch_state(State.GR1_CB1_TO_PM)
                else:
                    self.switch_state(State.GR1_CB1_TO_CB3) 
        
        elif self.state == State.GR1_CB1_TO_PM:
            if self.run_gr1():
                self.switch_state(State.PM)
                self.switch_status("CB1", Status.BLOCKED)

        elif self.state == State.PM:
            if self.run_pm():
                self.switch_state(State.GR1_PM_TO_CB3)

        elif self.state == State.GR1_PM_TO_CB3:
            if self.run_gr1():
                State.CB3_TO_WH.value[1] = Status.FREE
                self.switch_state(State.CB3_TO_WH)

        elif self.state == State.GR1_CB1_TO_CB3:
            if self.run_gr1():
                self.switch_state(State.CB3_TO_WH)

        elif self.state == State.CB3_TO_WH:
            if self.run_cb3():
                if self.config["with_WH"]:
                    self.switch_state(State.WH_STORE)
                    self.switch_status("CB3", Status.BLOCKED)
                else:
                    self.switch_state(State.CB3_TO_CB4)
        
        elif self.state == State.WH_STORE:
            if self.run_wh_store():
                self.switch_state(State.WH_RETRIEVE)

        elif self.state == State.WH_RETRIEVE:
            if self.run_wh_retrieve():
                self.switch_state(State.CB3_TO_CB4)
        
        elif self.state == State.CB3_TO_CB4:
            if self.run_cb3():
                self.switch_state(State.CB4)

        elif self.state == State.CB4:
            if self.run_cb4():
                self.switch_state(State.GR3)

        elif self.state == State.GR3:
            if self.run_gr3():
                self.switch_state(State.CB5)

        elif self.state == State.CB5:
            if self.run_cb5():
                self.switch_state(State.SL)

        elif self.state == State.SL:
            if self.run_sl():
                self.switch_state(State.VG2)

        elif self.state == State.VG2:
            if self.run_vg2():
                self.switch_state(State.END)

    def switch_state(self, state: State, wait=False):
        '''Switch to given state and save state start time.
        
        :state: state Enum to switch to
        :wait: waits for input bevor switching
        '''
        if state.value[1] == Status.FREE:
            if self.state == self.config["end_at"]:
                state = State.END
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

    
    ####################################################################################################
    # Methods that control the different states for the
    def test(self) -> False:
        wh: Warehouse = self.machines.get("WH")
        if wh == None:
            wh = Warehouse(self.revpi, "WH", self.FACTORY)
            self.machines[wh.name] = wh
            # wh.init(for_store=True)
            wh.store_product(color=self.config["color"])

    def run_init(self) -> False:
        for gr in ["GR1", "GR2", "GR3"]:
            self.machines[gr] = GripRobot(self.revpi, gr, Position(-1, -1, -1))
            self.machines[gr].init(to_end=True)
        for vg in ["VG1", "VG2"]:
            self.machines[vg] = VacRobot(self.revpi, vg, Position(-1, -1, -1))
            self.machines[vg].init(to_end=True)
        self.machines["WH"] = Warehouse(self.revpi, "WH", factory=self.FACTORY)
        self.machines["WH"].init(to_end=True)
        State.INIT.value[1] = Status.FREE
        self.switch_state(State.END)

    def run_cb1(self) -> False:
        machine: Conveyor = self.machines.get("CB1")
        if machine == None:
            machine = Conveyor(self.revpi, "CB1")
            self.machines[machine.name] = machine
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", f"{machine.name}_SENS_END")
            return True

    def run_cb3(self) -> False:
        machine: Conveyor = self.machines.get("CB3")
        if machine == None:
            machine = Conveyor(self.revpi, "CB3")
            self.machines[machine.name] = machine          
        
        elif self.state == State.CB3_TO_WH and machine.is_stage(1):
            if self.config["with_WH"] == False:
                machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END", end_machine=False)
                machine.stage = 0
                self.state = State.CB3_TO_CB4
            else:
                machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END")
                return True
        
        elif self.state == State.CB3_TO_CB4 and machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor="CB4_SENS_START")
            return True
        
    def run_cb4(self) -> False:
        machine: Conveyor = self.machines.get("CB4")
        if machine == None:
            machine = Conveyor(self.revpi, "CB4")
            self.machines[machine.name] = machine            
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END", start_sensor="CB3_SENS_END", stop_delay_in_ms=100)
            return True
        
    def run_cb5(self) -> False:
        machine: Conveyor = self.machines.get("CB5")
        if machine == None:
            machine = Conveyor(self.revpi, "CB5")
            self.machines[machine.name] = machine            
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END", end_machine=False)
        elif machine.is_stage(2):
            machine.run_to_stop_sensor("FWD", stop_sensor="SL_CB_SENS_START")
            return True

    def run_gr1(self) -> False:
        machine: GripRobot = self.machines.get("GR1")
        if machine == None:
            machine = GripRobot(self.revpi, "GR1", Position(-1, -1, 1400))
            self.machines[machine.name] = machine
            machine.init()
        elif machine.ready_for_next:
            machine.ready_for_next = False

        # move from cb1 to cb2
        elif self.state == State.GR1_CB1_TO_PM:
            if machine.is_stage(1):
                # move to cb1 (6s)
                machine.reset_claw()
                machine.move_to_position(Position(245, 65, 1600), ignore_moving_pos=True)
            # Wait for cb1 to finish
            elif machine.is_stage(2) and self.ready_for_transport == "CB1":
                # move down
                machine.move_to_position(Position(-1, -1, 2100))
            elif machine.is_stage(3):
                # grip product, move to cb2, release product
                machine.move_product_to(Position(3845, 78, 1950), sensor="CB1_SENS_END")
            elif machine.is_stage(4):
                # move up and end state
                machine.move_to_position(Position(-1, -1, 1600))
                machine.stage = 0
                return True

        # move from cb2 to cb3    
        elif self.state == State.GR1_PM_TO_CB3:
            if machine.is_stage(1) and machine.state == State_3D.INIT:
                # move to cb2 if new gr1
                machine.reset_claw()
                machine.move_to_position(Position(3845, 78, 1400), ignore_moving_pos=True)
                machine.stage = 0
            if machine.is_stage(1):
                # move down
                machine.move_to_position(Position(-1, -1, 2000))
            elif machine.is_stage(2):
                # grip product, move to cb3, release product
                machine.move_product_to(Position(2305, 40, 1550), sensor="CB2_SENS_START")
            elif machine.is_stage(3):
                # move back to init
                machine.init(to_end=True)
                return True

        #move from cb1 to cb3    
        elif self.state == State.GR1_CB1_TO_CB3:
            if machine.is_stage(1):
                # move to cb1 (6s)
                machine.reset_claw()
                machine.move_to_position(Position(245, 65, 1600), ignore_moving_pos=True)
            # Wait for cb1 to finish
            elif machine.is_stage(2) and self.ready_for_transport == "CB1":
                # move down
                machine.move_to_position(Position(-1, -1, 2100))
            elif machine.is_stage(3):
                # grip product, move to cb3, release product
                machine.move_product_to(Position(2305, 40, 1550), sensor="CB1_SENS_END")
            elif machine.is_stage(4):
                # move back to init
                machine.init(to_end=True)
                return True

    def run_gr2(self) -> False:
        machine: GripRobot = self.machines.get("GR2")
        if machine == None:
            machine = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            self.machines[machine.name] = machine
            machine.init()
            self.run_mps()

        elif machine.is_stage(1):
            # get product from plate
            machine.GRIPPER_OPENED = 5
            machine.reset_claw()
            machine.move_to_position(Position(2245, 55, 3450))
        elif machine.is_stage(2):
                # grip
                machine.GRIPPER_CLOSED = 10
                machine.grip()
        elif machine.is_stage(3):
            # move product to mps
            machine.move_to_position(Position(1365, 24, 1700))
        elif machine.is_stage(4):
                # release
                machine.GRIPPER_OPENED = 9
                machine.release()
        elif machine.is_stage(5):
            # move back to init
            machine.init(to_end=True)
            return True

    def run_gr3(self) -> False:
        machine: GripRobot = self.machines.get("GR3")
        if machine == None:
            machine = GripRobot(self.revpi, "GR3", Position(-1, -1, 1400))
            self.machines[machine.name] = machine
            machine.init()
        elif machine.ready_for_next:
            machine.ready_for_next = False

        elif machine.is_stage(1):
            # move to cb4
            machine.reset_claw()
            machine.move_to_position(Position(437, 43, 1400), ignore_moving_pos=True)

        elif machine.is_stage(2) and self.ready_for_transport == "CB4":
            # move down
            machine.move_to_position(Position(-1, -1, 1900))
        elif machine.is_stage(3):
            # grip product, move to cb5, release product
            machine.move_product_to(Position(1865, 10, 1800), sensor="CB4_SENS_END")
        elif machine.is_stage(4):
            # move back to init
            machine.init(to_end=True)
            return True
    
    def run_vg2(self) -> False:
        machine: VacRobot = self.machines.get("VG2")
        if machine == None:
            machine = VacRobot(self.revpi, "VG2", Position(-1, -1, 400))
            self.machines[machine.name] = machine
            machine.init()

        elif machine.is_stage(1) and self.config["color"] == "WHITE":
            # move to white
            machine.move_to_position(Position(0, 1450, 1200))
        elif machine.is_stage(1) and self.config["color"] == "RED":
            # move to red
            machine.move_to_position(Position(130, 1560, 1200))
        elif machine.is_stage(1) and self.config["color"] == "BLUE":
            # move to blue
            machine.move_to_position(Position(255, 1750, 1200))

        elif machine.is_stage(2) and self.ready_for_transport == "SL":
            machine.move_to_position(Position(-1, -1, 1400))
        elif machine.is_stage(3):
            # grip product, move to out, release product
            machine.move_product_to(Position(1000, 800, 1750), sensor=f"SL_SENS_{self.config['color']}")
        elif machine.is_stage(4):
            # move back to init
            machine.init(to_end=True)
            return True

    def run_pm(self) -> False:
        pm: PunchMach = self.machines.get("PM")
        cb: Conveyor = self.machines.get("CB2")
        if pm == None:
            pm = PunchMach(self.revpi, "PM")
            self.machines[pm.name] = pm
        if cb == None:
            cb = Conveyor(self.revpi, "CB2")
            self.machines[cb.name] = cb
        
        elif cb.is_stage(1):
            cb.run_to_stop_sensor("FWD", stop_sensor="PM_SENS_IN", end_machine=False)

        elif pm.is_stage(1):
            pm.run(out_stop_sensor="CB2_SENS_END")

        elif cb.is_stage(2) and self.ready_for_transport == "PM":
            cb.run_to_stop_sensor("BWD", stop_sensor="CB2_SENS_START", start_sensor="PM_SENS_IN", stop_delay_in_ms=150, end_machine=False)

        elif cb.is_stage(3) and pm.is_stage(2):
            pm.end_machine = True
            cb.end_machine = True
            return True

    def run_mps(self) -> False:
        machine: MPStation = self.machines.get("MPS")
        if machine == None:
            machine = MPStation(self.revpi, "MPS")
            self.machines[machine.name] = machine
            machine.init()
        elif machine.start_next_machine:
            return True
        
        elif machine.is_stage(1):
            machine.run(with_oven=self.config["with_oven"])

    def run_sl(self) -> False:
        machine: SortLine = self.machines.get("SL")
        if machine == None:
            machine = SortLine(self.revpi, "SL")
            self.machines[machine.name] = machine
        elif machine.start_next_machine:
            return True
        
        elif machine.is_stage(1):
            machine.run(color=self.config["color"])

    def run_wh_store(self) -> False:
        wh: Warehouse = self.machines.get("WH")
        vg: VacRobot = self.machines.get("VG1")
        if wh == None:
            wh = Warehouse(self.revpi, "WH", self.FACTORY)
            self.machines[wh.name] = wh
            wh.init(for_store=True)
        if vg == None:
            vg = VacRobot(self.revpi, "VG1", Position(-1, -1, 200))
            self.machines[vg.name] = vg
            vg.init()

        if vg.is_stage(1):
            # move to cb3
            vg.move_to_position(Position(97, 815, 1150), ignore_moving_pos=True)
        elif vg.is_stage(2) and self.ready_for_transport == "CB3":
            # move down
            vg.move_to_position(Position(-1, -1, 1250))
        elif vg.is_stage(3):
            # grip product, move to wh
            vg.move_product_to(Position(1785, 1080, 400), sensor="CB3_SENS_END", release=False)

        # wait for warehouse to have a carrier
        elif vg.is_stage(4) and wh.ready_for_next:
            # move down a bit
            vg.move_to_position(Position(-1, -1, 700))
        elif vg.is_stage(5):
            # release product
            vg.release()
            # move up a bit
            vg.move_to_position(Position(-1, -1, 400))

        elif wh.is_stage(1) and vg.is_stage(7):
            wh.store_product(color=self.config["color"])

        elif vg.is_stage(7) and self.config["end_at"] == State.WH_STORE:
                vg.init(to_end=False)

        elif wh.is_stage(2):
            wh.init(to_end=True)
            if self.config["end_at"] == State.WH_STORE:
                vg.end_machine = True
            else:
                vg.stage = 1
            return True

    def run_wh_retrieve(self) -> False:
        wh: Warehouse = self.machines.get("WH")
        vg: VacRobot = self.machines.get("VG1")
        if wh == None:
            wh = Warehouse(self.revpi, "WH", self.FACTORY)
            self.machines[wh.name] = wh
            wh.init(for_retrieve=True)
        if vg == None:
            vg = VacRobot(self.revpi, "VG1", Position(-1, -1, 200))
            self.machines[vg.name] = vg
            vg.init()

        if wh.is_stage(1):
            wh.retrieve_product(color=self.config["color"])
        
        if vg.is_stage(1) and vg.state == State_3D.INIT:
            # move to wh if new vg1
            vg.move_to_position(Position(1785, 1080, 400), ignore_moving_pos=True)
            vg.stage = 0
        elif vg.is_stage(1) and wh.is_stage(2):
            # move down
            vg.move_to_position(Position(-1, -1, 700))
        elif vg.is_stage(2):
            # grip product, move to cb3, release product
            vg.move_product_to(Position(97, 815, 1150))

        # return wh to init position
        elif wh.is_stage(2) and vg.ready_for_next:
            wh.init(to_end=False)

        elif vg.is_stage(3):
            # move back to init
            vg.init(to_end=True)
            wh.end_machine = True
            return True

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
            "with_PM": True,
            "with_WH": True,
            "color": "RED",
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
            "start_when": "no",
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

    running = True
    while(running and not MainLoop.error_exception_in_machine):
        running = False
        for config, thread in zip(configs, threads):

            if thread.is_alive():
                running = True

            elif config["start_when"] == stage:
                running = True
                if not config["running"]:
                    log.critical(f"Start: {config['name']}")
                    thread.start()
                    config["running"] = True
                elif not thread.is_alive():
                    config["running"] = False
                    stage = config["name"]
                    log.critical(f"Stop: {config['name']}")
        
        sleep(1)

    log.critical("End of program")
    revpi.exit()
