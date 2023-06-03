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
from sort_line import SortLine
from warehouse import Warehouse, ShelfPos

class State(Enum):
    INIT = 0

    CB1 = 11
    CB2 = 12
    CB3 = 13
    CB3_1 = 131
    CB3_2 = 132
    CB4 = 14
    CB5 = 15

    GR1 = 21
    GR1_1 = 211
    GR1_2 = 212
    GR2 = 22
    GR3 = 23

    VG = 30
    VG1 = 31
    VG1_1 = 311
    VG1_2 = 312
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

        self.main = Machine(self.revpi, "Main")
        self.state = self.main.switch_state(State.GR2)
        self.machines = {"Main": self.main}
        log.info("Main: Start Mainloop")

        while(not self.main.error_exception_in_machine and not self.main.end_machine and not self.exit_handler.was_called):
            self.mainloop()
            sleep(0.02)

      
    def mainloop(self):
        for machine in self.machines.values():
            if machine.error_exception_in_machine:
                self.state = self.main.switch_state(State.ERROR)
                log.error("Error in Mainloop")
                self.exit_handler.stop_factory()
                self.main.error_exception_in_machine = True
                return
            
        for machine in self.machines.values():
            if machine.end_machine:
                self.machines.pop(machine.name)
                break

        if self.state == State.END:
            self.main.ready_for_transport = True
            if not self.end():
                return
            log.info("End of program")
            self.main.end_machine = True
            self.revpi.exit()
            return

        if self.state == State.TEST:
            if self.test():
                self.state = self.main.switch_state(State.INIT)

        elif self.state == State.GR2:
            if self.run_gr2():
                self.state = self.main.switch_state(State.MPS)

        elif self.state == State.MPS:
            if self.run_mps():
                self.state = self.main.switch_state(State.CB1)

        elif self.state == State.CB1:
            if self.run_cb1():
                self.state = self.main.switch_state(State.GR1_1)
        
        elif self.state == State.GR1_1:
            if self.run_gr1():
                self.state = self.main.switch_state(State.PM)

        elif self.state == State.PM:
            if self.run_pm():
                self.state = self.main.switch_state(State.GR1_2)

        elif self.state == State.GR1_2:
            if self.run_gr1():
                self.state = self.main.switch_state(State.CB3_1)

        elif self.state == State.CB3_1:
            if self.run_cb3():
                self.state = self.main.switch_state(State.VG1_1)
        
        elif self.state == State.VG1_1:
            if self.run_vg1():
                self.state = self.main.switch_state(State.WH)
        
        elif self.state == State.WH:
            if self.run_wh():
                self.state = self.main.switch_state(State.VG1_2)
        
        elif self.state == State.VG1_2:
            if self.run_vg1():
                self.state = self.main.switch_state(State.CB3_2)
        
        elif self.state == State.CB3_2:
            if self.run_cb3():
                self.state = self.main.switch_state(State.CB4)

        elif self.state == State.CB4:
            if self.run_cb4():
                self.state = self.main.switch_state(State.GR3)

        elif self.state == State.GR3:
            if self.run_gr3():
                self.state = self.main.switch_state(State.CB5)

        elif self.state == State.CB5:
            if self.run_cb5():
                self.state = self.main.switch_state(State.SL)

        elif self.state == State.SL:
            if self.run_sl():
                self.state = self.main.switch_state(State.VG2)

        elif self.state == State.VG2:
            if self.run_vg2():
                self.state = self.main.switch_state(State.END)


    ####################################################################################################
    # Methods that control the different states for the
    def test(self) -> False:
        try:
            self.gr2
        except:
            self.gr2 = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            # self.gr2.init(as_thread=True)

        if self.gr2.error_exception_in_machine:
            self.state = self.main.switch_state(State.ERROR)
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

                self.state = self.main.switch_state(State.END)
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
            self.machines[machine.name] = machine
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", f"{machine.name}_SENS_END", as_thread=True)
            return True

    def run_cb3(self) -> False:
        machine: Conveyor = self.machines.get("CB3")
        if machine == None:
            machine = Conveyor(self.revpi, "CB3")
            self.machines[machine.name] =  machine          
        
        elif self.state == State.CB3_1 and machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END", as_thread=True)
            return True
        
        elif self.state == State.CB3_2 and machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor="CB4_SENS_START", as_thread=True)
            return True
        
    def run_cb4(self) -> False:
        machine: Conveyor = self.machines["CB4"]
        if machine == None:
            machine = Conveyor(self.revpi, "CB4")
            self.machines[machine.name] =  machine            
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END", start_sensor="CB3_SENS_END", stop_delay_in_ms=100, as_thread=True)
            return True
        
    def run_cb5(self) -> False:
        machine: Conveyor = self.machines.get("CB5")
        if machine == None:
            machine = Conveyor(self.revpi, "CB5")
            self.machines[machine.name] =  machine            
        
        elif machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END", as_thread=True)
        elif machine.is_stage(2):
            machine.run_to_stop_sensor("FWD", stop_sensor="SL_CB_SENS_START", as_thread=True)
            return True

    def run_gr1(self) -> False:
        machine: GripRobot = self.machines.get("GR1")
        if machine == None:
            machine = GripRobot(self.revpi, "GR1", Position(-1, -1, 1400))
            self.machines[machine.name] =  machine
            machine.init(as_thread=True)

        # move from cb1 to cb2
        elif self.state == State.GR1_1:
            if machine.is_stage(1):
                # move to cb1 (6s)
                machine.reset_claw(as_thread=True)
                machine.move_to_position(Position(225, 60, 1600), ignore_moving_pos=True, as_thread=True)
            # Wait for cb1 to finish
            elif machine.is_stage(2) and self.is_ready_for_transport("CB1"):
                # get product from cb1
                machine.move_to_position(Position(-1, -1, 2100), as_thread=True)
            elif machine.is_stage(3):
                # grip
                machine.grip(as_thread=True)
            elif machine.is_stage(4):
                # move to cb2
                machine.move_to_position(Position(3835, 78, 2050), as_thread=True)
            elif machine.is_stage(5):
                # release
                machine.release(as_thread=True)
            elif machine.is_stage(6):
                # move up and end state
                machine.move_to_position(Position(-1, -1, 1600), as_thread=True)
                machine.stage = 0
                return True

        # move from cb2 to cb3    
        elif self.state == State.GR1_2:
            if machine.is_stage(1):
                # move down
                machine.move_to_position(Position(-1, -1, 2050), as_thread=True)
            elif machine.is_stage(2):
                # grip
                machine.grip(as_thread=True)
            elif machine.is_stage(3):
                # move product to cb3
                machine.move_to_position(Position(2380, 0, 2050), as_thread=True)
            elif machine.is_stage(4):
                # release
                machine.release(as_thread=True)
            elif machine.is_stage(5):
                # move back to init
                machine.init(to_end=True, as_thread=True)
                return True

        #move from cb1 to cb3    
        elif self.state == State.GR1:
            if machine.is_stage(1):
                # move to cb1 (6s)
                machine.reset_claw(as_thread=True)
                machine.move_to_position(Position(225, 60, 1600), ignore_moving_pos=True, as_thread=True)
            # Wait for cb1 to finish
            elif machine.is_stage(2) and self.is_ready_for_transport("CB1"):
                # get product from cb1
                machine.move_to_position(Position(-1, -1, 2100), as_thread=True)
            elif machine.is_stage(3):
                # grip
                machine.grip(as_thread=True)
            elif machine.is_stage(3):
                # move product to cb3
                machine.move_to_position(Position(2380, 0, 2050), as_thread=True)
            elif machine.is_stage(4):
                # release
                machine.release(as_thread=True)
            elif machine.is_stage(5):
                # move back to init
                machine.init(to_end=True, as_thread=True)
                return True

    def run_gr2(self) -> False:
        machine: GripRobot = self.machines.get("GR2")
        if machine == None:
            machine = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            self.machines[machine.name] =  machine
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # get product from plate
            machine.reset_claw(as_thread=True)
            machine.move_to_position(Position(2225, 53, 3450), as_thread=True)
        elif machine.is_stage(2):
                # grip
                machine.grip(as_thread=True)
        elif machine.is_stage(3):
            # move product to mps
            machine.move_to_position(Position(1340, 36, 1500), as_thread=True)
        elif machine.is_stage(4):
                # release
                machine.release(as_thread=True)
        elif machine.is_stage(5):
            # move back to init
            machine.init(to_end=True, as_thread=True)
            return True

    def run_gr3(self) -> False:
        machine: GripRobot = self.machines.get("GR3", Position(-1, -1, 1400))
        if machine == None:
            machine = GripRobot(self.revpi, "GR3")
            self.machines[machine.name] =  machine
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # move to cb4
            machine.reset_claw(as_thread=True)
            machine.move_to_position(Position(440, 40, 1400), ignore_moving_pos=True, as_thread=True)
        elif machine.is_stage(2) and self.is_ready_for_transport("CB4"):
            self.is_ready_for_transport("CB3")
            # get product from cb4
            machine.move_to_position(Position(-1, -1, 1900), as_thread=True)
        elif machine.is_stage(3):
                # grip
                machine.grip(as_thread=True)
        elif machine.is_stage(4):
            # move product to cb5
            machine.move_to_position(Position(1870, 0, 1800), as_thread=True)
        elif machine.is_stage(5):
                # release
                machine.release(as_thread=True)
        elif machine.is_stage(6):
            # move back to init
            machine.init(to_end=False, as_thread=True)
            return True
    
    def run_vg1(self) -> False:
        machine: VacRobot = self.machines.get("VG1")
        if machine == None:
            machine = VacRobot(self.revpi, "VG1", Position(-1, -1, 200))
            self.machines[machine.name] =  machine
            machine.init(as_thread=True)

        elif self.state == State.VG1_1:
            if machine.is_stage(1):
                # move to cb3
                machine.move_to_position(Position(85, 790, 1150), as_thread=True)
            elif machine.is_stage(2) and self.is_ready_for_transport("CB3"):
                # get product from CB3
                machine.move_to_position(Position(-1, -1, 1300), as_thread=True)
            elif machine.is_stage(3):
                # grip
                machine.grip(as_thread=True)
            elif machine.is_stage(4):
                # move product to wh
                machine.move_to_position(Position(1770, 1075, 700), as_thread=True)
            elif machine.is_stage(5):
                # release
                machine.release(as_thread=True)
            elif machine.is_stage(6):
                # move up a bit
                machine.move_to_position(Position(-1, -1, 500), as_thread=True)
                machine.stage = 0
                return True

        elif self.state == State.VG1_2:
            if machine.is_stage(1):
                # get product from WH
                machine.move_to_position(Position(1770, 1075, 500), as_thread=True)
            elif machine.is_stage(1):
                # get product from WH
                machine.move_to_position(Position(-1, -1, 800), as_thread=True)
            elif machine.is_stage(2):
                # grip
                machine.grip(as_thread=True)
            elif machine.is_stage(3):
                # move product to cb3
                machine.move_to_position(Position(85, 790, 1150), as_thread=True)
            elif machine.is_stage(5):
                # release
                machine.release(as_thread=True)
            elif machine.is_stage(5):
                # move back to init
                machine.init(to_end=True, as_thread=True)
                return True
    
    def run_vg2(self) -> False:
        machine: VacRobot = self.machines.get("VG2")
        if machine == None:
            machine = VacRobot(self.revpi, "VG2", Position(-1, -1, 400))
            self.machines[machine.name] =  machine
            machine.init(as_thread=True)

        elif machine.is_stage(1): # and self.machines["SL").color == "WHITE":
            # self.machines["SL").end_machine = True
            # move to white
            machine.move_to_position(Position(0, 1450, 1400), as_thread=True)
        # elif machine.is_stage(1) and self.machines["SL").color == "RED":
        #     self.machines["SL").end_machine = True
        #     # move to blue
        #     machine.move_to_position(Position(130, 1560, 1400), as_thread=True)
        # elif machine.is_stage(1) and self.machines["SL").color == "BLUE":
        #     self.machines["SL").end_machine = True
        #     # move to red
        #     machine.move_to_position(Position(255, 1750, 1400), as_thread=True)
        elif machine.is_stage(2):
                # grip
                machine.grip(as_thread=True)
        elif machine.is_stage(3):
            # move product to out
            machine.move_to_position(Position(1000, 800, 1750), grip_bevor_moving=True, as_thread=True)
        elif machine.is_stage(4):
                # release
                machine.release(as_thread=True)
        elif machine.is_stage(5):
            # move back to init
            machine.init(to_end=True, as_thread=True)
            return True

    def run_pm(self) -> False:
        machine: PunchMach = self.machines.get("PM")
        if machine == None:
            machine = PunchMach(self.revpi, "PM")
            self.machines[machine.name] =  machine
        elif machine.ready_for_transport:
            machine.end_machine = True
            return True
        
        elif machine.is_stage(0):
            machine.run(as_thread=True)            

    def run_mps(self) -> False:
        machine: MPStation = self.machines.get("MPS")
        if machine == None:
            machine = MPStation(self.revpi, "MPS")
            self.machines[machine.name] =  machine
        elif machine.start_next_machine:
            return True
        
        elif machine.is_stage(1):
            machine.run(as_thread=True)

    def run_sl(self) -> False:
        machine: MPStation = self.machines.get("SL")
        if machine == None:
            machine = SortLine(self.revpi, "SL")
            self.machines[machine.name] =  machine
        elif machine.start_next_machine:
            self.is_ready_for_transport("CB5")
            return True
        
        elif machine.is_stage(1):
            machine.run(as_thread=True)

    def run_wh(self) -> False:
        machine: Warehouse = self.machines.get("WH")
        if machine == None:
            machine = Warehouse(self.revpi, "WH")
            self.machines[machine.name] =  machine
            machine.init(as_thread=True)
        elif machine.ready_for_transport:
            return True

        elif machine.is_stage(1):
            machine.store_product(ShelfPos.SHELF_1_1, as_thread=True)
        elif machine.is_stage(2):
            machine.retrieve_product(ShelfPos.SHELF_1_1, as_thread=True)

    def end(self) -> False:
        '''waits for any machines left running'''
        machine_running = False
        while(True):
            # check if there any machines left running
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
            self.main.end_machine
            return True

    def is_ready_for_transport(self, machine_name: str) -> bool:
        '''Returns the value of ready_for_transport for given machine.
        and if True set end_machine to True

        :machine_name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        ready_for_transport = False
        try:
            # try to get value
            ready_for_transport = self.machines[machine_name].ready_for_transport
        except:
            # if machine not found return True by default
            log.error(f"{machine_name} :Is not available")
            ready_for_transport = True

        if ready_for_transport:
            self.machines.pop(machine_name, False)

        return ready_for_transport
    

# Start RevPiApp app
if __name__ == "__main__":
    MainLoop()