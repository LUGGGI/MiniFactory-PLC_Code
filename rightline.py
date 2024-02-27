'''
Right line for MiniFactory project for machines:
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
__version__ = "2024.02.27"

from enum import Enum

from lib.logger import log
from lib.sensor import Sensor
from lib.conveyor import Conveyor
from lib.punch_mach import PunchMach
from lib.mp_station import MPStation
from lib.grip_robot import GripRobot, Position
from lib.vac_robot import VacRobot
from lib.sort_line import SortLine
from lib.warehouse import Warehouse
from lib.mainline import MainLine, Status, MainState
from lib.setup import Setup

class State(Enum):
    '''NAME = [ID, Status, Used_by]'''
    CB1 = [11, Status.FREE, "None"]
    CB3 = [13, Status.FREE, "None"]
    CB4 = [14, Status.FREE, "None"]
    CB4_TO_WH = [141, Status.FREE, "None"]
    CB4_TO_CB5 = [142, Status.FREE, "None"]
    CB5 = [15, Status.FREE, "None"]

    GR1 = [21, Status.FREE, "None"]
    GR2 = [22, Status.FREE, "None"]
    GR2_CB1_TO_CB3 = [221, Status.FREE, "None"]
    GR2_CB1_TO_PM = [222, Status.FREE, "None"]
    GR2_PM_TO_CB3 = [223, Status.FREE, "None"]
    GR3 = [23, Status.FREE, "None"]

    VG2 = [32, Status.FREE, "None"]

    MPS = [5, Status.FREE, "None"]
    PM = [6, Status.FREE, "None"]
    SL = [7, Status.FREE, "None"]
    WH = [8, Status.FREE, "None"]
    WH_STORE = [81, Status.FREE, "None"]
    WH_RETRIEVE = [82, Status.FREE, "None"]

    WAITING = [99, Status.FREE, "None"]
    TEST = [1000, Status.FREE, "None"]


class RightLine(MainLine):
    '''State loop and functions for right Factory.'''
    '''
    Methodes:
        run_...(): Calls the different modules.
        mainloop(): Switches between machines.
    Attributes:
        WAREHOUSE_CONTENT_FILE (str): File path to the file that saves the warehouse inventory.
    '''
    WAREHOUSE_CONTENT_FILE = "right_wh_content.json"

    def __init__(self, revpi, config: dict):
        '''Initializes MiniFactory control loop.'''
        super().__init__(revpi, config, State)
        
        global log
        self.log = log.getChild(f"{self.line_name}(Main)")

        self.state = MainState.INIT

    def mainloop(self):
        '''Switches the line states.'''
        # if line is waiting for the next machine
        if self.waiting_for_state != None:
            return

        if self.state == State.TEST:
            if self.test():
                return
            
        if self.state == MainState.INIT:
            if self.run_init():
                self.switch_state(MainState.END, wait=False)

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

        elif self.state == State.GR2_PM_TO_CB3 or self.state == State.GR2_CB1_TO_CB3:
            if self.run_gr2():
                self.switch_state(State.CB3)

        elif self.state == State.CB3:
            if self.run_cb3():
                if self.config.get("with_WH"):
                    self.switch_state(State.CB4_TO_WH)
                else:
                    self.switch_state(State.CB4_TO_CB5)

        elif self.state == State.CB4_TO_WH:
            if self.run_cb4():
                self.switch_state(State.WH_STORE)
        
        elif self.state == State.WH_STORE:
            if self.run_wh_store():
                self.switch_state(State.WH_RETRIEVE)

        elif self.state == State.WH_RETRIEVE:
            if self.run_wh_retrieve():
                self.switch_state(State.CB4_TO_CB5)
        
        elif self.state == State.CB4_TO_CB5:
            if self.run_cb4():
                self.switch_state(State.CB5)

        elif self.state == State.CB5:
            if self.run_cb5():
                self.switch_state(State.GR3)

        elif self.state == State.GR3:
            if self.run_gr3():
                self.switch_state(State.SL)

        elif self.state == State.SL:
            if self.run_sl():
                self.switch_state(State.VG2)

        elif self.state == State.VG2:
            if self.run_vg2():
                self.switch_state(MainState.END)

    ####################################################################################################
    # Methods that control the different states for the
    def test(self) -> False:
        pass


    def run_init(self) -> False:
        if self.position == 0:
            self.position = 1
            for gr in ["GR1", "GR2", "GR3"]:
                self.machines[gr] = GripRobot(self.revpi, gr, self.name, Position(-1, -1, -1))
                self.machines[gr].init(to_end=True)
            for vg in ["VG1", "VG2"]:
                self.machines[vg] = VacRobot(self.revpi, vg, self.name, Position(-1, -1, -1))
                self.machines[vg].init(to_end=True)
            self.machines["WH"] = Warehouse(self.revpi, "WH", self.name, self.WAREHOUSE_CONTENT_FILE)
            self.machines["WH"].init(to_end=True)

        if self.machines.__len__() <= 0:
            return True


    def run_cb1(self) -> False:
        cb: Conveyor = self.get_machine("CB1", Conveyor)
        
        if cb.is_position(1):
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", f"{cb.name}_SENS_END", stop_delay_in_ms=200)
        if cb.is_position(2):
            cb.switch_state(MainState.END)
            return True
        
        # init GR2
        if self.state != self.config["end_at"] and (State.GR2_CB1_TO_CB3.value[1] == Status.FREE or State.GR2_CB1_TO_CB3.value[2] == self.name):
            self.run_gr2()


    def run_cb3(self) -> False:
        cb: Conveyor = self.get_machine("CB3", Conveyor)
        
        if cb.is_position(1):
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")

        if self.is_end_state():
            cb.switch_state(MainState.END)
            return True

        if cb.is_position(2) and (
                (self.config.get("with_WH") and self.state_is_free(State.CB4_TO_WH)) or
                (not self.config.get("with_WH") and self.state_is_free(State.CB4_TO_WH))
            ):
            cb.run_to_stop_sensor("FWD", stop_sensor="CB4_SENS_START", end_machine=True)
            return True
        
        # init wh
        if self.config.get("with_WH") and not self.is_end_state() and self.state_is_free(State.WH_STORE):
            self.run_wh_store()    
        

    def run_cb4(self) -> False:
        cb: Conveyor = self.get_machine("CB4", Conveyor)
        
        if self.state == State.CB4_TO_WH:
            if cb.is_position(1) and self.state_is_free(State.WH_STORE):
                self.product_at = cb.name
                cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_START", stop_delay_in_ms=100)
            elif cb.is_position(2):
                cb.switch_state(MainState.END)
                return True
            
            # init wh
            if not self.is_end_state() and self.state_is_free(State.WH_STORE):
                self.run_wh_store()

        elif self.state == State.CB4_TO_CB5:
            if cb.is_position(1):
                self.product_at = cb.name
                cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")

            if self.is_end_state():
                cb.switch_state(MainState.END)
                return True
            elif cb.is_position(2) and self.state_is_free(State.CB5):
                cb.run_to_stop_sensor("FWD", stop_sensor="CB5_SENS_START", end_machine=True)
                return True


    def run_cb5(self) -> False:
        cb: Conveyor = self.get_machine("CB5", Conveyor)
        
        if cb.is_position(1):
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END", stop_delay_in_ms=200)
        elif cb.is_position(2) and State.SL.value[1] == Status.FREE:
            cb.switch_state(MainState.END)
            return True
        # init gr3
        if self.state != self.config["end_at"] and (State.GR3.value[1] == Status.FREE or State.GR3.value[2] == self.name):
            self.run_gr3()


    def run_gr1(self) -> False:
        gr: GripRobot = self.get_machine("GR1", GripRobot, Position(-1, 0, 1400))
        if gr.is_position(0):
            gr.init()
            if State.MPS.value[1] == Status.FREE:
                self.run_mps()

        elif gr.is_position(1):
            # get product from plate
            gr.GRIPPER_OPENED = 5
            gr.reset_claw()
            gr.move_to_position(Position(1400, 0, 1400), ignore_moving_pos=True)
        elif gr.is_position(2):
            gr.move_to_position(Position(1925, 10, 3650), ignore_moving_pos=True)
        elif gr.is_position(3):
            # grip product
            gr.grip()
        elif gr.is_position(4):
            self.product_at = gr.name
            # move to mps
            gr.move_to_position(Position(900, 0, 1400), ignore_moving_pos=True)
        elif gr.is_position(5):
            gr.move_to_position(Position(535, 0, 1400))
        elif gr.is_position(6) and (State.MPS.value[1] == Status.FREE or State.MPS.value[2] == self.name):
            # move to tray
            gr.move_to_position(Position(-1, 82, -1))
        elif gr.is_position(7):
            # release product
            gr.GRIPPER_OPENED = 10
            gr.release(with_check_sens="MPS_SENS_OVEN")
        elif gr.is_position(8):
            # move back to init
            gr.GRIPPER_OPENED = 9 # reset to default
            gr.init(to_end=True)
            return True


    def run_gr2(self) -> False:
        gr: GripRobot = self.get_machine("GR2", GripRobot, Position(-1, -1, 1700))
        if gr.is_position(0):
            gr.init()

        # move gr to cb1
        if self.state == State.CB1 or self.state == State.GR2_CB1_TO_PM or self.state == State.GR2_CB1_TO_CB3:
            if gr.is_position(1):
                # move to cb1
                gr.reset_claw()
                gr.move_to_position(Position(145, 72, 1700), ignore_moving_pos=True)

            if gr.is_position(2):
                # get product from cb1, (move down, grip product, move up)
                gr.get_product(2650, sensor="CB1_SENS_END")

        # move product to pm
        if self.state == State.GR2_CB1_TO_PM:
            if gr.is_position(3):
                self.product_at = gr.name
                # move to cb2
                gr.move_to_position(Position(3710, 5, 1700))
            elif gr.is_position(4):
                # move down
                gr.move_to_position(Position(-1, -1, 2500))
            elif gr.is_position(5):
                # release product
                gr.release()
            elif gr.is_position(6):
                # move up and continue with next machine
                gr.move_to_position(Position(-1, 20, 1700))
                gr.position = 1
                return True
            return

        # get product from pm 
        if self.state == State.PM or self.state == State.GR2_PM_TO_CB3:
            if gr.is_position(1):
                # move to pm if not already there
                gr.reset_claw()
                gr.move_to_position(Position(3710, 20, 1700), ignore_moving_pos=True)
            
            if gr.is_position(2) and self.state == State.GR2_PM_TO_CB3:
                # get product from pm (move down, grip product, move up)
                gr.get_product(2500, sensor="CB2_SENS_START")

        # move product to cb3
        if self.state == State.GR2_CB1_TO_CB3 or self.state == State.GR2_PM_TO_CB3:
            if gr.is_position(3):
                self.product_at = gr.name
                # move to cb3
                gr.move_to_position(Position(1960, 10, 2500))
            elif gr.is_position(4) and self.state_is_free(State.CB3):
                # release product
                gr.release()
            elif gr.is_position(5):
                # move back to init
                gr.init(to_end=True)
                return True


    def run_gr3(self) -> False:
        gr: GripRobot = self.get_machine("GR3", GripRobot, Position(-1, -1, 1800))
        if gr.is_position(0):
            gr.init()

        elif gr.is_position(1):
            # move to cb5
            gr.reset_claw()
            gr.move_to_position(Position(140, 3, 1800), ignore_moving_pos=True)

        # if product ready get it
        elif gr.is_position(2) and self.state == State.GR3:
            # move down, grip product, move up
            gr.get_product(2450, sensor="CB5_SENS_END")
        elif gr.is_position(3):
            self.product_at = gr.name
            # move to cb5
            gr.move_to_position(Position(1970, 62, 1800))
        elif gr.is_position(4) and State.SL.value[1] == Status.FREE:
            # move down
            gr.move_to_position(Position(-1, -1, 2300))
        elif gr.is_position(5):
            # release product
            gr.release()
        elif gr.is_position(6):
            # move back to init
            gr.init(to_end=True)
            return True
    

    def run_vg2(self) -> False:
        vg: VacRobot = self.get_machine("VG2", VacRobot, Position(-1, -1, 1100))
        if vg.is_position(0):
            vg.init()

        elif vg.is_position(1) and self.config["color"] == "WHITE":
            # move to white
            vg.move_to_position(Position(875, 700, 1400))
        elif vg.is_position(1) and self.config["color"] == "RED":
            # move to red
            vg.move_to_position(Position(725, 875, 1400))
        elif vg.is_position(1) and self.config["color"] == "BLUE":
            # move to blue
            vg.move_to_position(Position(600, 1200, 1400))

        elif vg.is_position(2) and self.state == State.VG2:
            vg.get_product(1600, sensor=f"SL_SENS_{self.config['color']}")
        elif vg.is_position(3):
            self.product_at = vg.name
            # move to out
            vg.move_to_position(Position(0, 300, 1750))
        elif vg.is_position(4):
            # release product
            vg.release()
        elif vg.is_position(5):
            # move back to init
            vg.init(to_end=True)
            return True


    def run_pm(self) -> False:
        pm: PunchMach = self.get_machine("PM", PunchMach)
        cb: Conveyor = self.get_machine("CB2", Conveyor)
        
        if cb.is_position(1):
            self.switch_status(State.GR2_PM_TO_CB3, Status.WAITING)
            self.product_at = cb.name
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{cb.name}_SENS_END")
        elif cb.is_position(2):
            cb.run_to_stop_sensor("FWD", stop_sensor=f"{pm.name}_SENS_IN")
            self.product_at = pm.name
            pm.run(out_stop_sensor=f"{cb.name}_SENS_END")

        elif cb.is_position(3) and pm.ready_for_transport:
            self.product_at = cb.name
            cb.run_to_stop_sensor("BWD", stop_sensor=f"{cb.name}_SENS_START", stop_delay_in_ms=200)

        elif cb.is_position(4) and pm.is_position(2):
            pm.switch_state(MainState.END)
            cb.switch_state(MainState.END)
            return True
        
        if pm.ready_for_transport:
            # init GR2
            if not self.is_end_state() and self.state_is_free(State.GR2_PM_TO_CB3):
                self.run_gr2()


    def run_mps(self) -> False:
        mps: MPStation = self.get_machine("MPS", MPStation)
        if mps.is_position(0):
            mps.init()
        
        elif mps.is_position(1):
            self.product_at = mps.name
            mps.run(with_oven=self.config.get("with_oven"), with_saw=self.config.get("with_saw"))
        elif mps.is_position(2) and State.CB1.value[1] == Status.FREE:
            if self.is_end_state():
                mps.switch_state(MainState.END)
                return True
            mps.run_to_out()
            return True


    def run_sl(self) -> False:
        sl: SortLine = self.get_machine("SL", SortLine)
        if self.state != self.config["end_at"] and sl.start_next_machine:
            self.run_vg2()
        
        if sl.is_position(1):
            self.product_at = sl.name
            sl.run(color=self.config["color"])
        if sl.is_position(2):
            sl.switch_state(MainState.END)
            return True

    def run_wh_store(self) -> False:
        wh: Warehouse = self.get_machine("WH", Warehouse, self.WAREHOUSE_CONTENT_FILE)
        vg: VacRobot = self.get_machine("VG1", VacRobot, Position(-1, -1, 0))
        if wh.is_position(0):
            wh.init(for_store=True)
        if vg.is_position(0):
            vg.init()

        if vg.is_position(1):
            # move to cb4_start
            vg.move_to_position(Position(0, 1450, 1150), ignore_moving_pos=True)

        elif vg.is_position(2) and self.state == State.WH_STORE:
            # move down, grip product, move up
            vg.get_product(1450, sensor="CB4_SENS_START")
        elif vg.is_position(3):
            self.product_at = vg.name
            # move to wh
            vg.move_to_position(Position(1800, 140, 0), ignore_moving_pos=True)

        # wait for warehouse to have a carrier
        elif vg.is_position(4) and wh.ready_for_product == True:
            # move down a bit
            vg.move_to_position(Position(-1, -1, 500))
        elif vg.is_position(5):
            # release product
            vg.release()
            # move up a bit
            vg.move_to_position(Position(-1, -1, 0))

        elif wh.is_position(1) and vg.is_position(7):
            self.product_at = wh.name
            wh.store_product(color=self.config["color"])

        elif vg.is_position(7) and self.config["end_at"] == State.WH_STORE:
                vg.init(to_end=False)

        elif wh.is_position(2):
            if self.config["end_at"] == State.WH_STORE:
                wh.init(to_end=True)
                vg.switch_state(MainState.END)
            else:
                wh.position = 1
                vg.position = 2
            return True


    def run_wh_retrieve(self) -> False:
        wh: Warehouse = self.get_machine("WH", Warehouse, self.WAREHOUSE_CONTENT_FILE)
        vg: VacRobot = self.get_machine("VG1", VacRobot, Position(-1, -1, 0))
        if wh.is_position(0):
            wh.init(for_retrieve=True)
        if vg.is_position(0):
            vg.init()

        if wh.is_position(1):
            self.product_at = wh.name
            wh.retrieve_product(color=self.config["color"])
        if vg.is_position(1):
            # move to wh if new vg1
            vg.move_to_position(Position(1800, 140, 0), ignore_moving_pos=True)
        elif vg.is_position(2) and (wh.is_position(2) or wh.is_position(3)):
            # move down, grip product, move up
            vg.get_product(550)
        elif vg.is_position(3):
            self.product_at = vg.name
            # move to cb4_start
            vg.move_to_position(Position(0, 1450, 1100), ignore_moving_pos=True)
            wh.init(to_end=False)

        elif vg.is_position(4) and State.CB4_TO_CB5.value[1] == Status.FREE:
            # move down
            vg.move_to_position(Position(-1, -1, 1400))
        elif vg.is_position(5):
            # release product
            vg.release(with_check_sens="CB4_SENS_START")
        elif vg.is_position(6):      
            # move back to init
            vg.init(to_end=True)
            wh.switch_state(MainState.END)
            return True
        

if __name__ == "__main__":
    # Start and run the factory
    setup = Setup(State, RightLine, "Right")
    setup.run_factory()
