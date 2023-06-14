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
__version__ = "2023.06.09"

from time import sleep
from enum import Enum
import threading
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator
from conveyor import Conveyor
from punch_mach import PunchMach
from mp_station import MPStation
from grip_robot import GripRobot, Position, State as State_3D
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

    VG1 = 31
    VG1_1 = 311
    VG1_2 = 312
    VG2 = 32

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
            self.revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.img")
        self.revpi.mainloop(blocking=False)

        self.exit_handler = ExitHandler(self.revpi)

        self.main = Machine(self.revpi, "Main")
        self.state = self.main.switch_state(State.VG1_1)
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
                self.state = self.main.switch_state(State.MPS, True)
                pass

        elif self.state == State.MPS:
            if self.run_mps():
                self.state = self.main.switch_state(State.CB1, True)

        elif self.state == State.CB1:
            if self.run_cb1():
                self.state = self.main.switch_state(State.GR1_1, True)
        
        elif self.state == State.GR1_1:
            if self.run_gr1():
                self.state = self.main.switch_state(State.PM, True)

        elif self.state == State.PM:
            if self.run_pm():
                self.state = self.main.switch_state(State.GR1_2, True)

        elif self.state == State.GR1_2:
            if self.run_gr1():
                self.state = self.main.switch_state(State.CB3_1, True)

        elif self.state == State.CB3_1:
            if self.run_cb3():
                self.state = self.main.switch_state(State.VG1_1, True)
        
        elif self.state == State.VG1_1:
            if self.run_vg1():
                self.state = self.main.switch_state(State.WH, True)
        
        elif self.state == State.WH:
            if self.run_wh():
                self.state = self.main.switch_state(State.VG1_2, True)
        
        elif self.state == State.VG1_2:
            if self.run_vg1():
                self.state = self.main.switch_state(State.CB3_2, True)
        
        elif self.state == State.CB3_2:
            if self.run_cb3():
                self.state = self.main.switch_state(State.CB4)

        elif self.state == State.CB4:
            if self.run_cb4():
                self.state = self.main.switch_state(State.GR3, True)

        elif self.state == State.GR3:
            if self.run_gr3():
                self.state = self.main.switch_state(State.CB5, True)

        elif self.state == State.CB5:
            if self.run_cb5():
                self.state = self.main.switch_state(State.SL, True)

        elif self.state == State.SL:
            if self.run_sl():
                self.state = self.main.switch_state(State.VG2, True)

        elif self.state == State.VG2:
            if self.run_vg2():
                self.state = self.main.switch_state(State.END)


    ####################################################################################################
    # Methods that control the different states for the
    def test(self) -> False:
        machine: GripRobot = self.machines.get("GR2")
        if machine == None:
            machine = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            self.machines[machine.name] = machine
            try:
                # machine.move_all_axes(Position(0, -1, -1))
                machine.__motor_rot.move_axis("CW", 0, 100, 50, machine.__encoder_rot, machine.name + "_REF_SW_ROTATION", 3, True)
                log.critical("1")
                machine.__motor_rot.join()
                log.critical("2")
            except:
                log.exception("Det")
            log.critical("END")
        

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
        
        elif self.state == State.CB3_1 and machine.is_stage(1):
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END")
            return True
        
        elif self.state == State.CB3_2 and machine.is_stage(1):
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
            machine.run_to_stop_sensor("FWD", stop_sensor=f"{machine.name}_SENS_END")
        elif machine.is_stage(2):
            machine.run_to_stop_sensor("FWD", stop_sensor="SL_CB_SENS_START")
            return True

    def run_gr1(self) -> False:
        machine: GripRobot = self.machines.get("GR1")
        if machine == None:
            machine = GripRobot(self.revpi, "GR1", Position(-1, -1, 1400))
            self.machines[machine.name] = machine
            machine.init(as_thread=True)

        # move from cb1 to cb2
        elif self.state == State.GR1_1:
            if machine.is_stage(1):
                # move to cb1 (6s)
                machine.reset_claw(as_thread=True)
                machine.move_to_position(Position(245, 65, 1600), ignore_moving_pos=True)
            # Wait for cb1 to finish
            elif machine.is_stage(2) and self.is_ready_for_transport("CB1"):
                # move down
                machine.move_to_position(Position(-1, -1, 2100))
            elif machine.is_stage(3):
                # grip product, move to cb2, release product
                machine.move_product_to(Position(3840, 78, 1950), sensor="CB1_SENS_END")
            elif machine.is_stage(4):
                # move up and end state
                machine.move_to_position(Position(-1, -1, 1600))
                machine.stage = 0
                return True

        # move from cb2 to cb3    
        elif self.state == State.GR1_2:
            if machine.is_stage(1) and machine.state == State_3D.INIT:
                # move to cb2 if new gr1
                machine.reset_claw(as_thread=True)
                machine.move_to_position(Position(3835, 78, 1400), ignore_moving_pos=True)
                machine.stage = 0
            if machine.is_stage(1):
                # move down
                machine.move_to_position(Position(-1, -1, 2000))
            elif machine.is_stage(2):
                # grip product, move to cb3, release product
                machine.move_product_to(Position(2380, 0, 2050), sensor="CB2_SENS_START")
            elif machine.is_stage(3):
                # move back to init
                machine.init(to_end=True)
                return True

        #move from cb1 to cb3    
        elif self.state == State.GR1:
            if machine.is_stage(1):
                # move to cb1 (6s)
                machine.reset_claw(as_thread=True)
                machine.move_to_position(Position(225, 60, 1600), ignore_moving_pos=True)
            # Wait for cb1 to finish
            elif machine.is_stage(2) and self.is_ready_for_transport("CB1"):
                # move down
                machine.move_to_position(Position(-1, -1, 2100))
            elif machine.is_stage(3):
                # grip product, move to cb3, release product
                machine.move_product_to(Position(2380, 0, 2050), sensor="CB1_SENS_END")
            elif machine.is_stage(5):
                # move back to init
                machine.init(to_end=True)
                return True

    def run_gr2(self) -> False:
        machine: GripRobot = self.machines.get("GR2")
        if machine == None:
            machine = GripRobot(self.revpi, "GR2", moving_position=Position(-1, 0, 1100))
            self.machines[machine.name] = machine
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # get product from plate
            machine.GRIPPER_OPENED = 5
            machine.reset_claw()
            machine.move_to_position(Position(2245, 54, 3450))
        elif machine.is_stage(2):
                # grip
                machine.GRIPPER_CLOSED = 11
                machine.grip(as_thread=True)
        elif machine.is_stage(3):
            # move product to mps
            machine.move_to_position(Position(1365, 24, 1700))
        elif machine.is_stage(4):
                # release
                machine.GRIPPER_OPENED = 9
                machine.release(as_thread=True)
        elif machine.is_stage(5):
            # move back to init
            machine.init(to_end=True)
            return True

    def run_gr3(self) -> False:
        machine: GripRobot = self.machines.get("GR3")
        if machine == None:
            machine = GripRobot(self.revpi, "GR3", Position(-1, -1, 1400))
            self.machines[machine.name] = machine
            machine.init(as_thread=True)

        elif machine.is_stage(1):
            # move to cb4
            machine.reset_claw(as_thread=True)
            machine.move_to_position(Position(440, 40, 1400), ignore_moving_pos=True)

        elif machine.is_stage(2) and self.is_ready_for_transport("CB4"):
            self.is_ready_for_transport("CB3")
            # move down
            machine.move_to_position(Position(-1, -1, 1900))
        elif machine.is_stage(3):
            # grip product, move to cb5, release product
            machine.move_product_to(Position(1870, 0, 1800), sensor="CB4_SENS_END")
        elif machine.is_stage(4):
            # move back to init
            machine.init(to_end=False)
            return True
    
    def run_vg1(self) -> False:
        machine: VacRobot = self.machines.get("VG1")
        if machine == None:
            machine = VacRobot(self.revpi, "VG1", Position(-1, -1, 200))
            self.machines[machine.name] = machine
            machine.init(as_thread=True)

        elif self.state == State.VG1_1:
            if machine.is_stage(1):
                # move to cb3
                machine.move_to_position(Position(97, 815, 1150), ignore_moving_pos=True)
            elif machine.is_stage(2) and self.is_ready_for_transport("CB3"):
                # move down
                machine.move_to_position(Position(-1, -1, 1250))
            elif machine.is_stage(3):
                # grip product, move to wh, release product
                machine.move_product_to(Position(1785, 1080, 700), sensor="CB3_SENS_END")
            elif machine.is_stage(4):
                # move up a bit
                machine.move_to_position(Position(-1, -1, 500))
                machine.stage = 0
                return True

        elif self.state == State.VG1_2:
            if machine.is_stage(1) and machine.state == State_3D.INIT:
                # move to wh if new vg1
                machine.move_to_position(Position(1785, 1080, 200), ignore_moving_pos=True)
                machine.stage = 0
            elif machine.is_stage(1):
                # move down
                machine.move_to_position(Position(-1, -1, 750))
            elif machine.is_stage(2):
                # grip product, move to cb3, release product
                machine.move_product_to(Position(85, 790, 1150))
            elif machine.is_stage(3):
                # move back to init
                machine.init(to_end=True)
                return True
    
    def run_vg2(self) -> False:
        machine: VacRobot = self.machines.get("VG2")
        if machine == None:
            machine = VacRobot(self.revpi, "VG2", Position(-1, -1, 400))
            self.machines[machine.name] = machine
            machine.init(as_thread=True)

            # DEBUG
            self.machines["SL"] = SortLine(self.revpi, "SL")
            self.machines["SL"].color = "WHITE"


        elif machine.is_stage(1) and self.machines["SL"].color == "WHITE":
            # move to white
            machine.move_to_position(Position(0, 1450, 1400))
        elif machine.is_stage(1) and self.machines["SL"].color == "RED":
            # move to red
            machine.move_to_position(Position(130, 1560, 1400))
        elif machine.is_stage(1) and self.machines["SL"].color == "BLUE":
            # move to blue
            machine.move_to_position(Position(255, 1750, 1400))
        elif machine.is_stage(2):
            # grip product, move to out, release product
            machine.move_product_to(Position(1000, 800, 1750), sensor=f"SL_SENS_{self.machines['SL'].color}")
            self.machines["SL"].end_machine = True
        elif machine.is_stage(3):
            # move back to init
            machine.init(to_end=True)
            return True

    def run_pm(self) -> False:
        machine: PunchMach = self.machines.get("PM")
        if machine == None:
            machine = PunchMach(self.revpi, "PM")
            self.machines[machine.name] = machine
        elif machine.ready_for_transport:
            machine.end_machine = True
            return True
        
        elif machine.is_stage(0):
            machine.run(as_thread=True)            

    def run_mps(self) -> False:
        machine: MPStation = self.machines.get("MPS")
        if machine == None:
            machine = MPStation(self.revpi, "MPS")
            self.machines[machine.name] = machine
        elif machine.start_next_machine:
            return True
        
        elif machine.is_stage(1):
            machine.run(as_thread=True)

    def run_sl(self) -> False:
        machine: SortLine = self.machines.get("SL")
        if machine == None:
            machine = SortLine(self.revpi, "SL")
            self.machines[machine.name] = machine
        elif machine.start_next_machine:
            self.is_ready_for_transport("CB5")
            return True
        
        elif machine.is_stage(1):
            machine.run(as_thread=True)

    def run_wh(self) -> False:
        machine: Warehouse = self.machines.get("WH")
        if machine == None:
            machine = Warehouse(self.revpi, "WH")
            self.machines[machine.name] = machine
            machine.init(as_thread=True)
        elif machine.ready_for_transport:
            return True

        elif machine.is_stage(1):
            machine.store_product()
        elif machine.is_stage(2):
            machine.retrieve_product(color="COLOR_UNKNOWN")

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
