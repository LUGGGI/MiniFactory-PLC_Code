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
__version__ = "2023.05.23"

from time import sleep
from enum import Enum
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator
from conveyor import Conveyor
from punch_mach import PunchMach
from mp_station import MPStation
from grip_robot import GripRobot, Position
from vac_robot import VacRobot
from warehouse import Warehouse, ShelfPos

class State(Enum):
    INIT = 0

    CB1 = 11
    CB2 = 12
    CB3 = 12
    CB3_1 = 121
    CB3_2 = 122
    CB4 = 12
    CB5 = 12

    GR1 = 21
    GR1_1 = 211
    GR1_2 = 212
    GR2 = 22
    GR3 = 23

    VG = 30
    VG1 = 31
    VG2 = 32

    INDX = 4
    MPS = 5
    PM = 6
    SL = 7
    WH = 8

    END = 100
    ERROR = 999
    TEST = 1000

class MainLoop:

    

    def __init__(self):
        # setup RevpiModIO
        try:
            self.revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            self.revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi\RevPi82247.img")
        self.revpi.mainloop(blocking=False)

        self.exit_handler = ExitHandler(self.revpi)

        self.machine = Machine(self.revpi, "Main")
        self.state = self.machine.switch_state(State.CB3_2)
        self.machines = {"Main": self.machine}

        while(not self.machine.error_exception_in_machine and not self.machine.ready_for_transport and not self.exit_handler.was_called):
            self.mainloop()
            sleep(0.02)

      
    def mainloop(self):
        for machine in self.machines.values():
            if machine.error_exception_in_machine:
                self.state = self.machine.switch_state(State.ERROR)
                log.error("Error in Mainloop")
                self.exit_handler.stop_factory()
                self.machine.error_exception_in_machine = True
                return

        if self.state == State.END:
            self.machine.ready_for_transport = True
            log.info("End of program")
            self.revpi.exit()
            return

        if self.state == State.TEST:
            if self.test():
                self.state = self.machine.switch_state(State.INIT)

        elif self.state == State.GR2:
            if self.run_gr2():
                self.state = self.machine.switch_state(State.MPS)

        elif self.state == State.MPS:
            if self.run_mps():
                self.state = self.machine.switch_state(State.CB1)

        elif self.state == State.CB1:
            if self.run_cb1():
                self.state = self.machine.switch_state(State.GR1_1)
        
        elif self.state == State.GR1_1:
            if self.run_gr1():
                self.state = self.machine.switch_state(State.PM)

        elif self.state == State.PM:
            if self.run_pm():
                self.state = self.machine.switch_state(State.GR1_2)

        elif self.state == State.GR1_2:
            if self.run_gr1():
                self.state = self.machine.switch_state(State.CB3_1)

        elif self.state == State.CB3_1:
            if self.run_cb3():
                self.state = self.machine.switch_state(State.VG1)
        
        elif self.state == State.VG1:
            if self.run_vg1():
                self.state = self.machine.switch_state(State.INIT)
        
        elif self.state == State.CB3_2:
            if self.run_cb3():
                self.state = self.machine.switch_state(State.CB4)

        elif self.state == State.CB4:
            if self.run_cb4():
                self.state = self.machine.switch_state(State.GR3)

        elif self.state == State.GR3:
            if self.run_gr3():
                self.state = self.machine.switch_state(State.INIT)

        {
        # elif self.state == State.CB1:
        #     if self.run_cb1():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.CB2:
        #     if self.run_cb2():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.CB3:
        #     if self.run_cb3():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.CB4:
        #     if self.run_cb4():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.CB5:
        #     if self.run_cb5():
        #         self.state = self.machine.switch_state(State.END)

        # elif self.state == State.GR1:
        #     if self.run_gr1():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.GR2:
        #     if self.run_gr2():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.GR3:
        #     if self.run_gr3():
        #         self.state = self.machine.switch_state(State.END)

        # elif self.state == State.VG:
        #     if self.run_vg():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.VG1:
        #     if self.run_vg1():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.VG2:
        #     if self.run_vg2():
        #         self.state = self.machine.switch_state(State.END)
        

        # elif self.state == State.INDX:
        #     if self.run_indx():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.MPS:
        #     if self.run_mps():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.PM:
        #     if self.run_pm():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.SL:
        #     if self.run_sl():
        #         self.state = self.machine.switch_state(State.END)
        # elif self.state == State.WH:
        #     if self.run_wh():
        #         self.state = self.machine.switch_state(State.END)
        }

    ####################################################################################################
    # Methods that control the different states for the
    def test(self) -> False:
        try:
            self.gr2
        except:
            self.gr2 = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            # self.gr2.init(as_thread=True)

        if self.gr2.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return False

        elif self.gr2.stage == 0:
            # get product from plate
            # self.gr2.move_to_position(Position(0, 0, 0), grip_bevor_moving=True, ignore_moving_pos=True, as_thread=True)
            try:
                self.gr2.motor_claw.run_to_encoder_start("OPEN", self.gr2.name + "_REF_SW_CLAW", self.gr2.encoder_claw)
                self.gr2.motor_claw.run_to_encoder_value("CLOSE", self.gr2.encoder_claw, self.gr2.GRIPPER_OPENED)
                log.error("1------------------------")
                sleep(0.5)
                self.gr2.motor_claw.run_to_encoder_value("OPEN", self.gr2.encoder_claw, 4)
                log.error("2------------------------")
                sleep(2)
                self.gr2.motor_claw.run_to_encoder_start("OPEN", self.gr2.name + "_REF_SW_CLAW", self.gr2.encoder_claw)
                sleep(2)
                self.gr2.motor_claw.run_to_encoder_value("CLOSE", self.gr2.encoder_claw, self.gr2.GRIPPER_OPENED)

                self.state = self.machine.switch_state(State.END)
                return
            except Exception as error:
                self.gr2.state = self.gr2.switch_state(State.ERROR)
                self.gr2.error_exception_in_machine = True
                log.exception(error)
                return

            return True
        # elif not self.gr2.thread.is_alive() and self.gr2.stage == 2:
        #     # get product from plate
        #     self.gr2.move_to_position(Position(300, 5, 300), grip_bevor_moving=True, ignore_moving_pos=True, as_thread=True)
        elif not self.gr2.thread.is_alive() and self.gr2.stage == 2:
            # move back to init
            self.gr2.init(as_thread=True)
            return True

    def run_cb1(self) -> False:
        machine: Conveyor = self.machines.get("CB1")
        if machine == None:
            machine = Conveyor(self.revpi, "CB1")
            self.machines.update({machine.name: machine})
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", f"{machine.name}_SENS_END", as_thread=True)
            return True

    def run_cb3(self) -> False:
        machine: Conveyor = self.machines.get("CB3")
        if machine == None:
            machine = Conveyor(self.revpi, "CB3")
            self.machines.update({machine.name: machine})
            self.machines.get("CB3").stage = 2            
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", f"{machine.name}_SENS_END", as_thread=True)
            return True
        
        elif machine.is_stage(2):
            machine.run_to_stop_sensor("FWD", "CB4_SENS_END", as_thread=True)
            return True
        
    def run_cb4(self) -> False:
        machine: Conveyor = self.machines.get("CB4")
        if machine == None:
            machine = Conveyor(self.revpi, "CB4")
            self.machines.update({machine.name: machine})            
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", f"{machine.name}_SENS_END", start_sensor="CB3_SENS_END", as_thread=True)
            return True

    def run_gr1(self) -> False:
        machine: GripRobot = self.machines.get("GR1")
        if machine == None:
            machine = GripRobot(self.revpi, "GR1")
            self.machines.update({machine.name: machine})
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # move to cb1 (6s)
            machine.move_to_position(Position(225, 60, 1600), ignore_moving_pos=True, as_thread=True)

        # Wait for cb1 to finish
        elif machine.is_stage(2) and self.machines.get("CB1").ready_for_transport:
            # get product from cb1
            machine.move_to_position(Position(225, 60, 2100), ignore_moving_pos=True, as_thread=True)
        elif machine.is_stage(3):
            # move product to cb2
            machine.move_to_position(Position(3825, 78, 2050), grip_bevor_moving=True, as_thread=True)
        elif machine.is_stage(4):
            # move up and wait for pm
            machine.move_to_position(Position(3825, 78, 1600), ignore_moving_pos=True, as_thread=True)
            return True
        
        elif machine.is_stage(5):
            # move down
            machine.move_to_position(Position(3850, 78, 2050), ignore_moving_pos=True, as_thread=True)
        elif machine.is_stage(6):
            # move product to cb3
            machine.move_to_position(Position(2380, 0, 2050), grip_bevor_moving=True, as_thread=True)
        elif machine.is_stage(7):
            # move back to init
            machine.init(as_thread=True)
            return True

    def run_gr2(self) -> False:
        machine: GripRobot = self.machines.get("GR2")
        if machine == None:
            machine = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            self.machines.update({machine.name: machine})
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # get product from plate
            machine.move_to_position(Position(2275, 66, 3250), grip_bevor_moving=False, as_thread=True)
        elif machine.is_stage(2):
            # move product to mps
            machine.move_to_position(Position(1340, 36, 1500), grip_bevor_moving=True, as_thread=True)
        elif machine.is_stage(3):
            # move back to init
            machine.init(as_thread=True)
            return True

    def run_gr3(self) -> False:
        machine: GripRobot = self.machines.get("GR3")
        if machine == None:
            machine = GripRobot(self.revpi, "GR3")
            self.machines.update({machine.name: machine})
            machine.init(as_thread=True)

        elif machine.is_stage(2):
            # get product from plate
            machine.move_to_position(Position(2275, 66, 3250), grip_bevor_moving=False, as_thread=True)
        elif machine.is_stage(2):
            # move product to mps
            machine.move_to_position(Position(1340, 36, 1500), grip_bevor_moving=True, as_thread=True)
        elif machine.is_stage(3):
            # move back to init
            machine.init(as_thread=True)
            return True
        
    
    def run_vg1(self) -> False:
        machine: VacRobot = self.machines.get("VG1")
        if machine == None:
            machine = VacRobot(self.revpi, "VG1", Position(-1, -1, 200))
            self.machines.update({machine.name: machine})
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # get product from plate
            machine.move_to_position(Position(85, 780, 1350), as_thread=True)
        elif machine.is_stage(2):
            # move product to mps
            self.machine.switch_state(State.TEST, True)
            machine.move_to_position(Position(1780, 1130, 700), grip_bevor_moving=True, as_thread=True)
        elif machine.is_stage(3):
            # move back to init
            self.machine.switch_state(State.TEST, True)
            machine.init(as_thread=True)
            return True

    def run_pm(self) -> False:
        machine: PunchMach = self.machines.get("PM")
        if machine == None:
            machine = PunchMach(self.revpi, "PM")
            self.machines.update({machine.name: machine})
        elif machine.ready_for_transport:
            return True
        
        elif machine.is_stage(0):
            machine.run(as_thread=True)            

    def run_mps(self) -> False:
        machine: MPStation = self.machines.get("MPS")
        if machine == None:
            machine = MPStation(self.revpi, "MPS")
            self.machines.update({machine.name: machine})
        elif machine.start_next_machine:
            return True
        
        elif machine.is_stage(0):
            machine.run(as_thread=True)
        
    def run_wh(self) -> False:
        machine: Warehouse = self.machines.get("WH")
        if machine == None:
            machine = Warehouse(self.revpi, "WH")
            self.machines.update({machine.name: machine})
        elif machine.start_next_machine:
            return True

        if machine.is_stage(0):
            # self.wh.test(as_thread=True)
            machine.store_product(ShelfPos.SHELF_1_1, as_thread=True)
        if machine.is_stage(1):
            machine.retrieve_product(ShelfPos.SHELF_1_1, as_thread=True)
            # self.wh.ready_for_transport
        

# Start RevPiApp app
if __name__ == "__main__":
    MainLoop()