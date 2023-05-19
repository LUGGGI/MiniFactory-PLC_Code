'''
Main Loop for MiniFactory project for machines:
Conveyor
PunchMach
Warehouse
VacRobot
GripRobot
SortLine
MPStation
Author: Lukas Beck
Date: 29.04.2023
'''
from time import sleep
from enum import Enum
from revpimodio2 import RevPiModIO

from logger import log
from sensor import Sensor
from actuator import Actuator
from machine import Machine
from conveyor import Conveyor
from punch_mach import PunchMach
from grip_robot import GripRobot, Position

class State(Enum):
    INIT = 0
    CB1 = 1
    CB2 = 2
    PM = 3
    GR1 = 4
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

        self.machine = Machine(self.revpi, "Main")
        self.state = self.machine.switch_state(State.TEST)

        while(True):
            if self.mainloop() == False:
                break
            sleep(1)

    def __del__(self):
        log.debug("End of program")
        sleep(1)
        self.revpi.exit(full=True)

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

        if self.state == State.ERROR:
            log.error("Error in Mainloop")
            return False
        elif self.state == State.END:
            return False
        return True
    ####################################################################################################
    # Methods that control the different states for the
    def state_gr1(self):
        if self.machine.state_is_init == False:
                self.gr1 = GripRobot(self.revpi, "GR1")
                self.gr1.init(as_thread=True)
                self.machine.state_is_init = True
        
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
             
        
        if self.gr1.error_exception_in_machine:
            self.state = self.machine.switch_state(State.ERROR)
        elif self.gr1.ready_for_transport:
            del self.gr1
            self.state = self.machine.switch_state(State.END)

    def state_cb1(self):
        if self.machine.state_is_init == False:
                self.cb1 = Conveyor(self.revpi, "CB1")
                self.cb1.run_for_time("FWD", "CB1_SENS_END", 10)

                self.start_cb2 = Sensor(self.revpi, "CB1_SENS_END")
                self.start_cb2.start_monitor()
                self.machine.state_is_init = True
        if self.cb1.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)
        elif self.start_cb2.is_detected():
            del self.cb1
            self.state = self.machine.switch_state(State.CB2)

    def state_cb2(self):
        if self.machine.state_is_init == False:
                self.cb2 = Conveyor(self.revpi, "CB2")
                self.cb2.run_to_stop_sensor("FWD", "CB2_SENS_END", 10)
                self.machine.state_is_init = True
        if self.cb2.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)
        elif self.cb2.ready_for_transport:
            del self.cb2
            self.state = self.machine.switch_state(State.END)

    def state_pm(self):
        if self.machine.state_is_init == False:
                self.pm = PunchMach(self.revpi, "PM")
                self.pm.run()
                self.machine.state_is_init = True
        if self.pm.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)
        elif self.pm.ready_for_transport:
            del self.pm
            self.state = self.machine.switch_state(State.END)

# Start RevPiApp app
if __name__ == "__main__":
    MainLoop()