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
from warehouse import Warehouse, ShelfPos

class State(Enum):
    INIT = 0
    CB1 = 1
    CB2 = 2
    PM = 3
    GR1 = 4
    MPS = 5
    WH = 6
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
        self.state = self.machine.switch_state(State.WH)

        while(not self.machine.error_exception_in_machine and not self.machine.ready_for_transport):
            self.mainloop()
                
            sleep(1)

      
    def mainloop(self):
        if self.state == State.TEST:
            
            motor = Actuator(self.revpi, "GR1")
            # try:
            #     motor.run_to_encoder_value("UP", Sensor(self.revpi, "GR1_VERTICAL_ENCODER"), 300, timeout_in_s=5)
            # except Exception as error:
            #     log.exception(error)

            gr1 = GripRobot(self.revpi, "GR1")
            try:
                gr1.move_axis(motor, 300, 100, 40, "UP", Sensor(self.revpi, "GR1_VERTICAL_ENCODER"), None, timeout_in_s=3)
            except Exception as error:
                log.exception(error)
            
            self.state = self.machine.switch_state(State.END)

            
        if self.state == State.GR1:
             self.state_gr1()

        if self.state == State.PM:
             self.state_pm()

        if self.state == State.CB1:
            self.state_cb1()

        if self.state == State.CB2:
            self.state_cb2()

        if self.state == State.MPS:
            self.state_mps()

        if self.state == State.WH:
            self.state_wh()

        if self.state == State.ERROR:
            log.error("Error in Mainloop")
            self.exit_handler.stop_factory()
            self.machine.error_exception_in_machine = True
        elif self.state == State.END:
            self.machine.ready_for_transport = True
            log.info("End of program")
            self.revpi.cleanup()


    ####################################################################################################
    # Methods that control the different states for the
    def state_gr1(self):
        if self.machine.state_is_init == False:
            self.gr1 = GripRobot(self.revpi, "GR1")
            self.gr1.init(as_thread=True)
            self.machine.state_is_init = True

        if self.gr1.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return
        elif self.gr1.ready_for_transport:
            del self.gr1
            self.state = self.machine.switch_state(State.END)
            return

        elif not self.gr1.thread.is_alive() and self.gr1.stage == 0:
            # get product from cb1
            self.gr1.move_to_position(Position(225, 60, 2050), at_product=False, as_thread=True)
            self.gr1.stage = 1
        elif not self.gr1.thread.is_alive() and self.gr1.stage == 1:
            # move product to cb3
            self.gr1.move_to_position(Position(2380, 0, 2050), at_product=True, as_thread=True)
            self.gr1.stage = 2
        elif not self.gr1.thread.is_alive() and self.gr1.stage == 2:
            # move product to cb2
            self.gr1.move_to_position(Position(3832, 0, 2050), at_product=True, as_thread=True)
            self.gr1.stage = 2

    def state_cb1(self):
        if self.machine.state_is_init == False:
            self.cb1 = Conveyor(self.revpi, "CB1")
            self.cb1.run_to_stop_sensor("FWD", "CB1_SENS_END")

            self.start_cb2 = Sensor(self.revpi, "CB1_SENS_END")
            self.start_cb2.start_monitor()
            self.machine.state_is_init = True

        if self.cb1.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return
        elif self.cb1.ready_for_transport:
            del self.cb1
            self.state = self.machine.switch_state(State.END)
            return

    def state_cb2(self):
        if self.machine.state_is_init == False:
            self.cb2 = Conveyor(self.revpi, "CB2")
            self.cb2.run_to_stop_sensor("FWD", "CB2_SENS_END")
            self.machine.state_is_init = True

        if self.cb2.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return
        elif self.cb2.ready_for_transport:
            del self.cb2
            self.state = self.machine.switch_state(State.END)
            return

    def state_pm(self):
        if self.machine.state_is_init == False:
            self.pm = PunchMach(self.revpi, "PM")
            self.pm.run()
            self.machine.state_is_init = True

        if self.pm.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return
        elif self.pm.ready_for_transport:
            del self.pm
            self.state = self.machine.switch_state(State.END)
            return

    def state_mps(self):
        if self.machine.state_is_init == False:
            self.mps = MPStation(self.revpi, "MPS")
            self.mps.run(as_thread=True)
            self.machine.state_is_init = True
    
        if self.mps.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return
        elif self.mps.ready_for_transport:
            del self.mps
            self.state = self.machine.switch_state(State.END)
            return
        
    def state_wh(self):
        if self.machine.state_is_init == False:
            self.wh = Warehouse(self.revpi, "WH")
            self.wh.init(as_thread=True)
            self.machine.state_is_init = True

        if self.wh.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
            return
        elif self.wh.ready_for_transport:
            del self.wh
            self.state = self.machine.switch_state(State.END)
            return

        if not self.wh.thread.is_alive() and self.wh.stage == 0:
            self.wh.test(as_thread=True)
            # self.wh.store_product(ShelfPos.SHELF_1_1, as_thread=True)
        if not self.wh.thread.is_alive() and self.wh.stage == 1:
            self.wh.retrieve_product(ShelfPos.SHELF_1_1, as_thread=True)
            # self.wh.ready_for_transport
        

# Start RevPiApp app
if __name__ == "__main__":
    MainLoop()