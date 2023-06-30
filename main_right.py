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
from main import MainLoop, Setup, Status

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


class MainRight(MainLoop):
    '''State loop and functions for right Factory
    
    run_...(): Calls the different modules
    '''
    FACTORY = "right"
    def __init__(self, revpi, name: str, config: dict, exit_handler: ExitHandler):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, name, config, exit_handler, State)
        self.state = State.INIT

    def mainloop(self):
        '''Switches the main states.'''
        self.mainloop_config()

        if self.state == State.TEST:
            if self.test():
                return
            
        if self.state == State.INIT:
            if self.run_init():
                self.switch_state(State.END, False)

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

        elif self.state == State.PM:
            if self.run_pm():
                self.switch_state(State.GR1_PM_TO_CB3)

        elif self.state == State.GR1_PM_TO_CB3:
            if self.run_gr1():
                self.switch_state(State.CB3_TO_WH)

        elif self.state == State.GR1_CB1_TO_CB3:
            if self.run_gr1():
                if self.config["with_WH"]:
                    self.switch_state(State.CB3_TO_WH)
                else:
                    self.switch_state(State.CB3_TO_CB4)

        elif self.state == State.CB3_TO_WH:
            if self.run_cb3():
                self.switch_state(State.WH_STORE)
        
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
        return True

    def run_cb1(self) -> False:
        cb: Conveyor = self.get_machine("CB1", Conveyor)
        
        if cb.is_stage(1):
            cb.run_to_stop_sensor("FWD", f"{cb.name}_SENS_END")
            return True

    def run_cb3(self) -> False:
        cb: Conveyor = self.get_machine("CB3", Conveyor)

        if self.state == State.CB3_TO_WH:
            if cb.is_stage(1) and State.WH_STORE == Status.FREE:
                cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
                return True

        elif self.state == State.CB3_TO_CB4:
            if cb.is_stage(1):
                cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END", end_machine=False)
            if cb.is_stage(2):
                cb.run_to_stop_sensor("FWD", stop_sensor="CB4_SENS_START")
                return True
        
    def run_cb4(self) -> False:
        cb: Conveyor = self.get_machine("CB4", Conveyor)         
        
        if cb.is_stage(1) and self.is_ready_for_transport("CB3"):
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END", stop_delay_in_ms=100)
            return True
        
    def run_cb5(self) -> False:
        cb: Conveyor = self.get_machine("CB5", Conveyor)           
        
        if cb.is_stage(1):
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END", end_machine=False)
        elif cb.is_stage(2):
            cb.run_to_stop_sensor("FWD", stop_sensor="SL_CB_SENS_START")
            return True

    def run_gr1(self) -> False:
        gr: GripRobot = self.get_machine("GR1", GripRobot, Position(-1, -1, 1400))

        # move from cb1 to cb2
        if self.state == State.GR1_CB1_TO_PM:
            if gr.is_stage(0):
                gr.init()
            elif gr.is_stage(1):
                # move to cb1 (6s)
                gr.reset_claw()
                gr.move_to_position(Position(245, 65, 1600), ignore_moving_pos=True)
            # Wait for cb1 to finish
            elif gr.is_stage(2) and self.is_ready_for_transport("CB1"):
                # move down
                gr.move_to_position(Position(-1, -1, 2100))
            elif gr.is_stage(3):
                # grip product, move to cb2
                gr.grip_and_move_to_position(Position(3845, 78, 1950), sensor="CB1_SENS_END")
            elif gr.is_stage(4) and State.PM.value[1] == Status.FREE:
                # release product
                gr.release()
            elif gr.is_stage(5):
                # move up and end_machine
                gr.move_to_position(Position(-1, -1, 1600))
                gr.end_machine = True
                return True

        # move from pm to cb3    
        elif self.state == State.GR1_PM_TO_CB3:
            # init if new gr1, should not happen in normal operation
            if gr.is_stage(0) and abs(Sensor(self.revpi, gr.name + "_ROTATION_ENCODER").get_current_value() - 3845) > 40:
                gr.init()
            elif gr.is_stage(1):
                # move to pm
                gr.reset_claw()
                gr.move_to_position(Position(3845, 78, 1400), ignore_moving_pos=True)

            if gr.is_stage(0) or gr.is_stage(2) and self.is_ready_for_transport("CB2"):
                # move down
                gr.move_to_position(Position(-1, -1, 2000))
            elif gr.is_stage(3):
                # grip product, move to cb3
                gr.grip_and_move_to_position(Position(2305, 40, 1550), sensor="CB2_SENS_START")
            elif gr.is_stage(4) and State.CB3_TO_WH.value[1] == Status.FREE:
                # release product
                gr.release()
            elif gr.is_stage(5):
                # move back to init
                gr.init(to_end=True)
                return True

        # move from cb1 to cb3    
        elif self.state == State.GR1_CB1_TO_CB3:
            if gr.is_stage(0):
                gr.init()
            if gr.is_stage(1):
                # move to cb1 (6s)
                gr.reset_claw()
                gr.move_to_position(Position(245, 65, 1600), ignore_moving_pos=True)
            # Wait for cb1 to finish
            elif gr.is_stage(2) and self.is_ready_for_transport("CB1"):
                # move down
                gr.move_to_position(Position(-1, -1, 2100))
            elif gr.is_stage(3):
                # grip product, move to cb3, release product
                gr.grip_and_move_to_position(Position(2305, 40, 1550), sensor="CB1_SENS_END")
            elif gr.is_stage(4) and State.CB3_TO_WH.value[1] == Status.FREE:
                # release product
                gr.release()
            elif gr.is_stage(5):
                # move back to init
                gr.init(to_end=True)
                return True

    def run_gr2(self) -> False:
        gr: GripRobot = self.get_machine("GR2", GripRobot, Position(-1, 0, 1100))
        if gr.is_stage(0):
            gr.init()
            self.run_mps()

        elif gr.is_stage(1):
            # get product from plate
            gr.GRIPPER_OPENED = 5
            gr.reset_claw()
            gr.move_to_position(Position(2245, 55, 3450))
        elif gr.is_stage(2):
            # grip product, move to mps
            gr.GRIPPER_CLOSED = 10
            gr.grip_and_move_to_position(Position(1365, 24, 1700))
        elif gr.is_stage(3) and State.MPS.value[1] == Status.FREE:
            # release product
            gr.GRIPPER_OPENED = 9
            gr.release()
        elif gr.is_stage(4):
            # move back to init
            gr.init(to_end=True)
            return True

    def run_gr3(self) -> False:
        gr: GripRobot = self.get_machine("GR3", GripRobot, Position(-1, -1, 1400))
        if gr.is_stage(0):
            gr.init()

        elif gr.is_stage(1):
            # move to cb4
            gr.reset_claw()
            gr.move_to_position(Position(437, 43, 1400), ignore_moving_pos=True)

        elif gr.is_stage(2) and self.ready_for_transport == "CB4":
            # move down
            gr.move_to_position(Position(-1, -1, 1900))
        elif gr.is_stage(3):
            # grip product, move to cb5, release product
            gr.grip_and_move_to_position(Position(1865, 10, 1800), sensor="CB4_SENS_END")
        elif gr.is_stage(4) and State.CB5.value[1] == Status.FREE:
            # release product
            gr.release()
        elif gr.is_stage(5):
            # move back to init
            gr.init(to_end=True)
            return True
    
    def run_vg2(self) -> False:
        vg: VacRobot = self.get_machine("VG2", VacRobot, Position(-1, -1, 400))
        if vg.is_stage(0):
            vg.init()

        elif vg.is_stage(1) and self.config["color"] == "WHITE":
            # move to white
            vg.move_to_position(Position(0, 1450, 1200))
        elif vg.is_stage(1) and self.config["color"] == "RED":
            # move to red
            vg.move_to_position(Position(142, 1560, 1200))
        elif vg.is_stage(1) and self.config["color"] == "BLUE":
            # move to blue
            vg.move_to_position(Position(255, 1750, 1200))

        elif vg.is_stage(2) and self.is_ready_for_transport("SL"):
            vg.move_to_position(Position(-1, -1, 1400))
        elif vg.is_stage(3):
            # grip product, move to out, release product
            vg.grip_and_move_to_position(Position(1000, 800, 1750), sensor=f"SL_SENS_{self.config['color']}")
        elif vg.is_stage(4):
            # release product
            vg.release()
        elif vg.is_stage(5):
            # move back to init
            vg.init(to_end=True)
            return True

    def run_pm(self) -> False:
        pm: PunchMach = self.get_machine("PM", PunchMach)
        cb: Conveyor = self.get_machine("CB2", Conveyor)
        
        if cb.is_stage(1):
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END", end_machine=False)
        elif cb.is_stage(2):
            cb.run_to_stop_sensor("FWD", stop_sensor="PM_SENS_IN", end_machine=False)

        elif pm.is_stage(1):
            pm.run(out_stop_sensor="CB2_SENS_END")

        elif cb.is_stage(3) and self.is_ready_for_transport("PM"):
            cb.run_to_stop_sensor("BWD", stop_sensor="CB2_SENS_START", stop_delay_in_ms=150, end_machine=False)

        elif cb.is_stage(4) and pm.is_stage(2):
            pm.end_machine = True
            cb.end_machine = True
            return True

    def run_mps(self) -> False:
        mps: MPStation = self.get_machine("MPS", MPStation)
        if mps.is_stage(0):
            mps.init()
        elif mps.start_next_machine:
            return True
        
        elif mps.is_stage(1):
            mps.run(with_oven=self.config["with_oven"])

    def run_sl(self) -> False:
        sl: SortLine = self.get_machine("SL", SortLine)
        if sl.start_next_machine:
            return True
        
        elif sl.is_stage(1):
            sl.run(color=self.config["color"])

    def run_wh_store(self) -> False:
        wh: Warehouse = self.get_machine("WH", Warehouse, self.FACTORY)
        vg: VacRobot = self.get_machine("VG1", VacRobot, Position(-1, -1, 200))
        if wh.is_stage(0):
            wh.init(for_store=True)
        if vg.is_stage(0):
            vg.init()

        if vg.is_stage(1):
            # move to cb3
            vg.move_to_position(Position(97, 815, 1150), ignore_moving_pos=True)
        elif vg.is_stage(2) and self.is_ready_for_transport("CB3"):
            # move down
            vg.move_to_position(Position(-1, -1, 1250))
        elif vg.is_stage(3):
            # grip product, move to wh
            vg.grip_and_move_to_position(Position(1785, 1080, 400), sensor="CB3_SENS_END", release=False)

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
        wh: Warehouse = self.get_machine("WH", Warehouse, self.FACTORY)
        vg: VacRobot = self.get_machine("VG1", VacRobot, Position(-1, -1, 200))
        if wh.is_stage(0):
            wh.init(for_retrieve=True)
        if vg.is_stage(0):
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
            vg.grip_and_move_to_position(Position(97, 815, 1150))

        # return wh to init position
        elif wh.is_stage(2) and vg.ready_for_next:
            wh.init(to_end=False)

        elif vg.is_stage(3):
            # move back to init
            vg.init(to_end=True)
            wh.end_machine = True
            return True
        

if __name__ == "__main__":
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
            "start_at": State.CB1,
            "end_at": State.WH_STORE,
            "with_oven": False,
            "with_PM": True,
            "with_WH": True,
            "color": "RED",
            "running": False
        },
        {
            "name": "2_Main", 
            "start_when": "no",
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

    setup = Setup()
    setup.main_loops: "list[MainRight]" = []

    for config in configs:
        setup.add_mainloop(config["name"], MainRight(setup.revpi, config["name"], config, setup.exit_handler))

    setup.run_factory(configs)