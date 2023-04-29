'''
Main Loop for MiniFactory project

Author: Lukas Beck
Date: 29.04.2023
'''
import threading
from time import sleep
from enum import Enum
from revpimodio2 import RevPiModIO

from logger import log
# from sensor import Sensor
from machine import Machine
from conveyor import Conveyor

class State(Enum):
    CB1_SET = 0
    CB1 = 1
    CB2_SET = 2
    CB2 = 3
    END = 4
    ERROR = 5

class MainLoop:
    def __init__(self):
        # setup RevpiModIO
        self.revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi\RevPi82247.img")

        self.machine = Machine(self.revpi, "Main")

        self.state = self.machine.switch_state(State.CB1_SET)

        while(True):
            if self.mainloop() == False:
                break
            sleep(1)

    def __del__(self):
        log.debug("End of program")
        sleep(1)
        self.revpi.exit(full=True)

    def mainloop(self):
        if self.state == State.CB1_SET:
            self.cb1 = Conveyor(self.revpi, "CB1")
            t_cb1 = threading.Thread(target=self.cb1.run_for_time, args=("FWD", "CB1_SENS_END", 10), name="CB1")
            t_cb1.start()
            self.state = self.machine.switch_state(State.CB1)
        elif self.state == State.CB1:
            if self.cb1.ready_for_transport:
                del self.cb1
                self.state = self.machine.switch_state(State.CB2_SET)
            elif self.cb1.error_no_product_found:
                self.state = self.machine.switch_state(State.ERROR)

        if self.state == State.CB2_SET:
            self.cb2 = Conveyor(self.revpi, "CB2")
            t_cb2 = threading.Thread(target=self.cb2.run_to_stop_sensor, args=("FWD", "CB2_SENS_END", 10), name="CB2")
            t_cb2.start()
            self.state = self.machine.switch_state(State.CB2)

        elif self.state == State.CB2:
            if self.cb2.ready_for_transport:
                del self.cb2
                self.state = self.machine.switch_state(State.END)
            elif self.cb2.error_no_product_found:
                self.state = self.machine.switch_state(State.ERROR)

        elif self.state == State.END:
            return False
        elif self.state == State.ERROR:
            log.error("Error in Mainloop")
            return False
        return True
    
    def state_cb1(self):
        if self.cb2.init == None:
            self.cb1 = Conveyor(self.revpi, "CB1")
            t_cb1 = threading.Thread(target=self.cb1.run_for_time, args=("FWD", "CB1_SENS_END", 10), name="CB1")
            t_cb1.start()
            self.cb2.init == True

        if self.cb1.ready_for_transport:
            self.state = self.machine.switch_state(State.CB2_SET)
        elif self.cb1.error_no_product_found:
            self.state = self.machine.switch_state(State.ERROR)

# Start RevPiApp app
if __name__ == "__main__":
    MainLoop()