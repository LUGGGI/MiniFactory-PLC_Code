'''
Left line for MiniFactory project for machines:
Conveyor
PunchMach
Warehouse
VacRobot
GripRobot
IndexLine
MPStation
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.11.22"

from enum import Enum

from lib.logger import log
from lib.sensor import Sensor
from lib.conveyor import Conveyor
from lib.punch_mach import PunchMach
from lib.mp_station import MPStation
from lib.grip_robot import GripRobot, Position
from lib.vac_robot import VacRobot
from lib.index_line import IndexLine
from lib.warehouse import Warehouse
from lib.mainline import MainLine, Status
from lib.setup import Setup

class State(Enum):
    '''NAME = [ID, Status, Used_by]'''
    INIT = [0, Status.FREE, "None"]

    CB1 = [11, Status.FREE, "None"]
    CB3_TO_WH = [131, Status.FREE, "None"]
    CB3_TO_CB4 = [132, Status.FREE, "None"]
    CB4 = [14, Status.FREE, "None"]
    CB5 = [15, Status.FREE, "None"]

    GR1 = [21, Status.FREE, "None"]
    GR2_CB1_TO_CB3 = [221, Status.FREE, "None"]
    GR2_CB1_TO_PM = [222, Status.FREE, "None"]
    GR2_PM_TO_CB3 = [223, Status.FREE, "None"]
    GR3 = [23, Status.FREE, "None"]

    INDX = [4, Status.FREE, "None"]
    MPS = [5, Status.FREE, "None"]
    PM = [6, Status.FREE, "None"]
    WH_STORE = [81, Status.FREE, "None"]
    WH_RETRIEVE = [82, Status.FREE, "None"]

    WAITING = [99, Status.FREE, "None"]
    END = [100, Status.FREE, "None"]
    ERROR = [999, Status.FREE, "None"]
    TEST = [1000, Status.FREE, "None"]


class LeftLine(MainLine):
    '''State loop and functions for left Factory.'''
    '''
    Methodes:
        mainloop(): Switches between machines.
        run_...(): Calls the different modules.
    Attributes:
        WAREHOUSE_CONTENT_FILE (str): File path to the file that saves the warehouse inventory.
    '''
    WAREHOUSE_CONTENT_FILE = "left_wh_content.json"

    def __init__(self, revpi, config: dict):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, config, State)
        
        global log
        self.log = log.getChild(f"{self.line_name}(Main)")

        self.state = State.INIT

    def mainloop(self):
        '''Switches the line states.'''
        # if line is waiting for the next machine
        if self.waiting_for_state != None:
            return

        if self.state == State.TEST:
            if self.test():
                return
            
        if self.state == State.INIT:
            if self.run_init():
                self.switch_state(State.END, wait=False)

        elif self.state == State.GR1:
            if self.run_gr1():
                self.switch_state(State.MPS)

        elif self.state == State.MPS:
            if self.run_mps():
                self.switch_state(State.CB1)

        elif self.state == State.CB1:
            if self.run_cb1():
                if self.config.get("with_PM"):
                    self.switch_state(State.GR2_CB1_TO_PM)
                else:
                    self.switch_state(State.GR2_CB1_TO_CB3) 
        
        elif self.state == State.GR2_CB1_TO_PM:
            if self.run_gr2():
                self.switch_state(State.PM)

        elif self.state == State.PM:
            if self.run_pm():
                self.switch_state(State.GR2_PM_TO_CB3)

        elif self.state == State.GR2_PM_TO_CB3:
            if self.run_gr2():
                if self.config.get("with_WH"):
                    self.switch_state(State.CB3_TO_WH)
                else:
                    self.switch_state(State.CB3_TO_CB4)

        elif self.state == State.GR2_CB1_TO_CB3:
            if self.run_gr2():
                if self.config.get("with_WH"):
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
                self.switch_state(State.CB5)

        elif self.state == State.CB5:
            if self.run_cb5():
                self.switch_state(State.INDX)

        elif self.state == State.INDX:
            if self.run_indx():
                self.switch_state(State.GR3)

        elif self.state == State.GR3:
            if self.run_gr3():
                self.switch_state(State.END)

    ####################################################################################################
    # Methods that control the different states for the
    def test(self) -> False:
        pass

    def run_init(self) -> False:
        if self.position == 0:
            self.position = 1
            self.switch_status(State.INIT, Status.RUNNING)
            for gr in ["GR1", "GR2", "GR3"]:
                self.machines[gr] = GripRobot(self.revpi, gr, self.name, Position(-1, -1, -1))
                self.machines[gr].init(to_end=True)
            for vg in ["VG"]:
                self.machines[vg] = VacRobot(self.revpi, vg, self.name, Position(-1, -1, -1))
                self.machines[vg].init(to_end=True)
            self.machines["WH"] = Warehouse(self.revpi, "WH", self.name, self.WAREHOUSE_CONTENT_FILE)
            self.machines["WH"].init(to_end=True)

        if self.machines.__len__() <= 0:
            self.switch_status(State.INIT, Status.FREE)
            return True

    def run_cb1(self) -> False:
        cb: Conveyor = self.get_machine("CB1", Conveyor)
        
        if cb.is_position(1):
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", f"{cb.name}_SENS_END")
        if cb.is_position(2):
            cb.end_conveyor()
            return True
        
        # init GR2
        if self.state != self.config["end_at"] and (State.GR2_CB1_TO_CB3.value[1] == Status.FREE or State.GR2_CB1_TO_CB3.value[2] == self.name):
            self.run_gr2()

    def run_cb3(self) -> False:
        cb: Conveyor = self.get_machine("CB3", Conveyor)
        
        if self.state == State.CB3_TO_WH:
            if cb.is_position(1) and State.WH_STORE.value[1] == Status.FREE:
                self.product_at = cb.name
                cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
            elif cb.is_position(2):
                cb.end_conveyor()
                return True
            # init wh
            if self.state != self.config["end_at"] and (State.WH_STORE.value[1] == Status.FREE or State.WH_STORE.value[2] == self.name):
                self.run_wh_store()

        elif self.state == State.CB3_TO_CB4:
            if cb.is_position(1):
                self.product_at = cb.name
                cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
            elif cb.is_position(2) and State.CB4.value[1] == Status.FREE:
                cb.run_to_stop_sensor("FWD", stop_sensor="CB4_SENS_START", end_machine=True)
                return True
        
    def run_cb4(self) -> False:
        cb: Conveyor = self.get_machine("CB4", Conveyor)         
        
        if cb.is_position(1):
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
        elif cb.is_position(2) and State.CB5.value[1] == Status.FREE:
            cb.run_to_stop_sensor("FWD", stop_sensor="CB5_SENS_START", end_machine=True)
            return True
    
    def run_cb5(self) -> False:
        cb: Conveyor = self.get_machine("CB5", Conveyor)           
        
        if cb.is_position(1):
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
        elif cb.is_position(2):
            cb.run_to_stop_sensor("FWD", stop_sensor="INDX_SENS_START", end_machine=True)
            return True

    def run_gr1(self) -> False:
        gr: GripRobot = self.get_machine("GR1", GripRobot, Position(-1, 0, 1100))
        if gr.is_position(0):
            gr.init()
            if State.MPS.value[1] == Status.FREE:
                self.run_mps()

        elif gr.is_position(1):
            # get product from plate
            gr.GRIPPER_OPENED = 5
            gr.reset_claw()
            gr.move_to_position(Position(1950, 73, 3000))
        elif gr.is_position(2):
            # grip product
            gr.grip()
        elif gr.is_position(3):
            self.product_at = gr.name
            # move to mps
            gr.move_to_position(Position(870, 0, 1000))
        elif gr.is_position(4) and (State.MPS.value[1] == Status.FREE or State.MPS.value[2] == self.name):
            # move to tray
            gr.move_to_position(Position(-1, 65, -1))
        elif gr.is_position(5):
            # release product
            gr.release()
        elif gr.is_position(6):
            # move back to init
            gr.init(to_end=True)
            return True

    def run_gr2(self) -> False:
        gr: GripRobot = self.get_machine("GR2", GripRobot, Position(-1, -1, 1400))
        if gr.is_position(0):
            gr.init()

        # move gr to cb1
        if self.state == State.CB1 or self.state == State.GR2_CB1_TO_PM or self.state == State.GR2_CB1_TO_CB3:
            if gr.is_position(1):
                # move to cb1 (6s)
                gr.reset_claw()
                gr.move_to_position(Position(280, 75, 2000), ignore_moving_pos=True)
        # get product from cb1
        if self.state == State.GR2_CB1_TO_PM or self.state == State.GR2_CB1_TO_CB3:
            if gr.is_position(2):
                # move down, grip product, move up
                gr.get_product(2450, sensor="CB1_SENS_END")

        # move product to pm
        if self.state == State.GR2_CB1_TO_PM:
            if gr.is_position(3):
                self.product_at = gr.name
                # move to cb2
                gr.move_to_position(Position(3665, 75, 1400))
            elif gr.is_position(4):
                # move down
                gr.move_to_position(Position(-1, -1, 1950))
            elif gr.is_position(5):
                # release product
                gr.release()
            elif gr.is_position(6):
                # move up and end_machine
                gr.move_to_position(Position(-1, -1, 1400))
                gr.position = 1
                return True
            return

        # move to pm if new gr
        if self.state == State.PM or self.state == State.GR2_PM_TO_CB3:
            if gr.is_position(1):
                # move to cb2
                gr.reset_claw()
                gr.move_to_position(Position(3665, 75, 1400), ignore_moving_pos=True)
        # get product from pm
        if self.state == State.GR2_PM_TO_CB3:
            if gr.is_position(2):
                # move down, grip product, move up
                gr.get_product(1950, sensor="CB2_SENS_START")

        # move product to cb3
        if self.state == State.GR2_CB1_TO_CB3 or self.state == State.GR2_PM_TO_CB3:
            if gr.is_position(3):
                self.product_at = gr.name
                # move to cb3
                gr.move_to_position(Position(1960, 0, 1950))
            elif gr.is_position(4) and State.CB3_TO_WH.value[1] == Status.FREE:
                if self.config.get("with_WH") and State.WH_STORE.value[1] != Status.FREE:
                    return
                # release product
                gr.release()
            elif gr.is_position(5):
                # move back to init
                gr.init(to_end=True)
                return True

    def run_gr3(self) -> False:
        gr: GripRobot = self.get_machine("GR3", GripRobot, Position(-1, -1, 1400))
        if gr.is_position(0):
            gr.init()

        elif gr.is_position(1):
            # move to cb4
            gr.reset_claw()
            gr.move_to_position(Position(1910, 30, 1300), ignore_moving_pos=True)

        # if product ready get it
        elif gr.is_position(2) and self.state == State.GR3:
            # move down, grip product, move up
            gr.get_product(2050)
        elif gr.is_position(3):
            self.product_at = gr.name
            # move to out
            gr.move_to_position(Position(120, 75, 3600))
        elif gr.is_position(4):
            # release product
            gr.release()
        elif gr.is_position(5):
            # move back to init
            gr.init(to_end=True)
            return True

    def run_pm(self) -> False:
        pm: PunchMach = self.get_machine("PM", PunchMach)
        cb: Conveyor = self.get_machine("CB2", Conveyor)
        
        if cb.is_position(1):
            self.switch_status("GR2", Status.BLOCKED)
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
        elif cb.is_position(2):
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{pm.name}_SENS_IN")
            self.product_at = pm.name
            pm.run(out_stop_sensor=f"{cb.name}_SENS_END")

        elif cb.is_position(3) and pm.ready_for_transport:
            self.product_at = cb.name
            cb.run_to_stop_sensor("BWD", stop_sensor=f"{cb.name}_SENS_START", stop_delay_in_ms=150)

        elif cb.is_position(4) and pm.is_position(2):
            pm.end_machine = True
            cb.end_conveyor()
            return True
        
        if pm.ready_for_transport:
            # init GR2
            if self.state != self.config["end_at"] and (State.GR2_PM_TO_CB3.value[1] == Status.FREE or State.GR2_PM_TO_CB3.value[2] == self.name):
                self.run_gr2()

    def run_mps(self) -> False:
        mps: MPStation = self.get_machine("MPS", MPStation)
        if mps.is_position(0):
            mps.init()
        
        elif mps.is_position(1):
            self.product_at = mps.name
            mps.run(with_oven=self.config.get("with_oven"), with_saw=self.config.get("with_saw"))
        elif mps.is_position(2) and State.CB1.value[1] == Status.FREE:
            mps.run_to_out()
            return True

    def run_indx(self) -> False:
        indx: IndexLine = self.get_machine("INDX", IndexLine)
        
        if indx.is_position(1):
            self.product_at = indx.name
            indx.run(with_mill=self.config.get("with_oven"), with_drill=self.config.get("with_oven"))
        elif indx.is_position(2):
            indx.end_machine = True
            return True
        
        if indx.start_next_machine:
            # init GR3
            if self.state != self.config["end_at"] and (State.GR3.value[1] == Status.FREE or State.GR3.value[2] == self.name):
                self.run_gr3()


    def run_wh_store(self) -> False:
        wh: Warehouse = self.get_machine("WH", Warehouse, self.WAREHOUSE_CONTENT_FILE)
        vg: VacRobot = self.get_machine("VG", VacRobot, Position(-1, -1, 0))
        if wh.is_position(0):
            wh.init(for_store=True)
        if vg.is_position(0):
            vg.init()

        if vg.is_position(1):
            # move to cb3
            vg.move_to_position(Position(0, 1900, 1000), ignore_moving_pos=True)

        elif vg.is_position(2) and self.state == State.WH_STORE:
            # move down, grip product, move up
            vg.get_product(1350, sensor="CB3_SENS_END")
        elif vg.is_position(3):
            self.product_at = vg.name
            # move to wh
            vg.move_to_position(Position(1815, 1440, 200))

        # wait for warehouse to have a carrier
        elif vg.is_position(4) and wh.ready_for_product == True:
            # move down a bit
            vg.move_to_position(Position(-1, -1, 500))
        elif vg.is_position(5):
            # release product
            vg.release()
            # move up a bit
            vg.move_to_position(Position(-1, -1, 200))

        elif wh.is_position(1) and vg.is_position(7):
            self.product_at = wh.name
            wh.store_product(color=self.config["color"])

        elif vg.is_position(7) and self.config["end_at"] == State.WH_STORE:
                vg.init(to_end=False)

        elif wh.is_position(2):
            if self.config["end_at"] == State.WH_STORE:
                wh.init(to_end=True)
                vg.end_machine = True
            else:
                wh.position = 1
                vg.position = 2
            return True

    def run_wh_retrieve(self) -> False:
        wh: Warehouse = self.get_machine("WH", Warehouse, self.WAREHOUSE_CONTENT_FILE)
        vg: VacRobot = self.get_machine("VG", VacRobot, Position(-1, -1, 0))
        if wh.is_position(0):
            wh.init(for_retrieve=True)
        if vg.is_position(0):
            vg.init()

        if wh.is_position(1):
            self.product_at = wh.name
            wh.retrieve_product(color=self.config["color"])
        if vg.is_position(1):
            # move to wh if new vg1
            vg.move_to_position(Position(1815, 1440, 200), ignore_moving_pos=True)
        elif vg.is_position(2) and (wh.is_position(2) or wh.is_position(3)):
            # move down, grip product, move up
            vg.get_product(500)
        elif vg.is_position(3):
            self.product_at = vg.name
            # move to cb3
            vg.move_to_position(Position(0, 1900, 1000))
            wh.init(to_end=False)

        elif vg.is_position(4) and State.CB3_TO_CB4.value[1] == Status.FREE:
            # move down
            vg.move_to_position(Position(-1, -1, 1350))
        elif vg.is_position(5):
            # release product
            vg.release()
        elif vg.is_position(6):
            if Sensor(self.revpi, "CB3_SENS_END", self.line_name).get_current_value() == False:
                vg.log.warning(f"{vg.name} :Product still at WH, trying again")
                vg.position = 0
            else:
                vg.position += 1
        elif vg.is_position(7):        
            # move back to init
            vg.init(to_end=True)
            wh.end_machine = True
            return True
        

if __name__ == "__main__":
    # Start and run the factory
    setup = Setup("left_config.json", "states.json", State, LeftLine)
    setup.run_factory()
