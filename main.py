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
from machine import Machine
from conveyor import Conveyor
from punch_mach import PunchMach

class State(Enum):
    CB1 = 1
    CB2 = 2
    PM = 3
    END = 100
    ERROR = 999

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
        self.state = self.machine.switch_state(State.PM)

        while(True):
            if self.mainloop() == False:
                break
            sleep(1)

    def __del__(self):
        log.debug("End of program")
        sleep(1)
        self.revpi.exit(full=True)

    def mainloop(self):
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
    def state_cb1(self):
        if self.machine.state_is_init == False:
                self.cb1 = Conveyor(self.revpi, "CB1")
                self.cb1.run_for_time("FWD", "CB1_SENS_END", 10)

                self.start_cb2 = Sensor(self.revpi, "CB1_SENS_END")
                self.start_cb2.start_monitor()
                self.machine.state_is_init = True
        elif self.start_cb2.is_detected():
            del self.cb1
            self.state = self.machine.switch_state(State.CB2)
        elif self.cb1.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)

    def state_cb2(self):
        if self.machine.state_is_init == False:
                self.cb2 = Conveyor(self.revpi, "CB2")
                self.cb2.run_to_stop_sensor("FWD", "CB2_SENS_END", 10)
                self.machine.state_is_init = True
        elif self.cb2.ready_for_transport:
            del self.cb2
            self.state = self.machine.switch_state(State.END)
        elif self.cb2.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)

    def state_pm(self):
        if self.machine.state_is_init == False:
                self.pm = PunchMach(self.revpi, "PM")
                self.pm.run()
                self.machine.state_is_init = True
        elif self.pm.ready_for_transport:
            del self.pm
            self.state = self.machine.switch_state(State.END)
        elif self.pm.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)

# Start RevPiApp app
if __name__ == "__main__":
    MainLoop()