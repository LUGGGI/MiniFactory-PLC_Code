'''
This module controls the Indexed Line with two Machining Stations (Mill and Drill), it inherits form machine

Author: Lukas Beck
Date: 18.04.2023
'''
from enum import Enum
from time import sleep
from logger import log
from sensor import Sensor
from motor import Motor, Direction
import machine
from conveyor import Conveyor

class State(Enum):
    INIT = 0
    TRANSPORT_TO_MILL = 0
    MILLING = 0        
    TRANSPORT_TO_DRILL = 0
    DRILLING = 0  
    TRANSPORT_TO_END = 0      
    END = 0
    ERROR = 0

class IndexLine(machine.Machine):
    '''Controls the drill and mill machine and the surrounding conveyors
    '''

    sensor_front = False
    sensor_back = False

    def __init__(self, direction):
        super().__init__()
        self.direction = direction
        self.state = self.switch_state(State.INIT)

        self.motor_mill = Motor("mill")
        self.motor_drill = Motor("drill")
        self.motor_pusher_in = Motor("pusher_in")
        self.motor_pusher_out = Motor("pusher_out")

        self.conv_in = Conveyor(sensor_check=Sensor("in"), motor=Motor("cv_in"), direction=Direction.BWD, max_transport_time=2)
        self.conv_mill = Conveyor(sensor_stop=Sensor("mill"), motor=Motor("cv_mill"), direction=Direction.BWD, max_transport_time=2)
        self.conv_drill = Conveyor(sensor_stop=Sensor("drill"), motor=Motor("cv_drill"), direction=Direction.BWD, max_transport_time=2)
        self.conv_out = Conveyor(sensor_check=Sensor("out1"), motor=Motor("cv_out"), direction=Direction.BWD, max_transport_time=2)

        # retract pusher
        self.motor_pusher_in.start(Direction.BWD)
        self.motor_pusher_out.start(Direction.BWD)
        sleep(1) # _DEBUG
        self.motor_pusher_in.stop()
        self.motor_pusher_out.stop()

        log.debug("Created DrillAndMill")
        self.state = self.switch_state(State.TRANSPORT_TO_MILL)

    def run(self):
        '''runs the drill and mill until end or error'''
        while not self.waiting_for_transport and not self.error_no_product_found:
            self.update()        

    def update(self):
        '''Call in a loop to update and change the state/action'''
        if self.state == State.TRANSPORT_TO_MILL:
            self.conv_in.run()

            self.motor_pusher_in.start(Direction.FWD)
            sleep(1) # _DEBUG
            self.motor_pusher_in.stop()

            self.conv_mill.run()

            self.state = self.switch_state(State.MILLING)
        
        if self.state == State.MILLING:
            self.motor_mill.start(Direction.FWD)
            sleep(1) # _DEBUG
            self.motor_mill.stop()

            self.state = self.switch_state(State.TRANSPORT_TO_DRILL)

        if self.state == State.TRANSPORT_TO_DRILL:
            self.conv_mill.run()
        
        if self.state == State.END:
            self.waiting_for_transport = True
            log.info("End of Conveyor")
        
        if self.state == State.ERROR:
            self.error_no_product_found = True
            log.error("Error in conveyor")

        sleep(1)