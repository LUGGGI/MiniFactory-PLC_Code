'''
This module controls the Warehouse, it inherits from machine

Author: Lukas Beck
Date: 18.05.2023
'''
import threading
from enum import Enum

from logger import log
from machine import Machine
from sensor import Sensor
from actuator import Actuator
from conveyor import Conveyor
 
class State(Enum):
    INIT = 0
    MOVING_TO_CB = 1
    MOVING_TO_RACK = 2
    GETTING_PRODUCT = 3
    SETTING_PRODUCT = 4
    CB_BWD = 4
    CB_FWD = 5
    END = 100
    ERROR = 999

class Warehouse(Machine):
    '''Controls the Warehouse
    
    store_product(): Stores a product at given position.
    retrieve_product(): Retrieves a product from given position.
    move_to_position(): Moves Crane given coordinates.
    move_axis(): Moves one axis to the given trigger value.
    '''

    POS_CB_HORIZONTAL = 0
    POS_CB_VERTICAL = 500

    

    def __init__(self, revpi, name: str):
        super().__init__(revpi, name)
        self.state = None

        self.REF_SW_ARM_FRONT = self.name + "_REF_SW_ARM_FRONT"
        self.REF_SW_ARM_BACK = self.name + "_REF_SW_ARM_BACK"

        self.move_threshold_hor = 40
        self.move_threshold_ver = 40

        # get conveyor
        self.cb = Conveyor(self.revpi, self.name + "_CB")

        # get encoder
        self.encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_ENCODER")
        self.encoder_ver = Sensor(self.revpi, self.name + "_VERTICAL_ENCODER")

        # get motors
        self.motor_loading = Actuator(self.revpi, self.name + "_ARM", "loading")
        self.motor_hor = Actuator(self.revpi, self.name + "_CRANE", "horizontal")
        self.motor_ver = Actuator(self.revpi, self.name + "_ARM", "vertical")

        log.debug("Created Warehouse: " + self.name)

    def __del__(self):
        log.debug("Destroyed Warehouse: " + self.name)

    def store_product(self, horizontal: int, vertical: int, as_thread=False):
        '''Stores a product at given position.

        :horizontal: horizontal coordinate
        :vertical: vertical coordinate
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.store_product, args=(horizontal, vertical), name=self.name)
            self.thread.start()
            return
        
        log.info("Store product at: " + str(f"({horizontal},{vertical})"))
        try:
            # move product to inside
            self.state = self.switch_state(State.CB_BWD)
            self.cb.run_to_stop_sensor("BWD", self.name + "_SENS_IN", as_thread=True)

            # move to cb
            self.state = self.switch_state(State.MOVING_TO_CB)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)
            self.move_to_position(self.POS_CB_HORIZONTAL, self.POS_CB_VERTICAL)
            self.cb.thread.join()

            # get product from cb
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, self.POS_CB_VERTICAL - 100)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)

            # move to given rack
            self.state = self.switch_state(State.MOVING_TO_RACK)
            self.move_to_position(horizontal, vertical - 100)

            # store product in rack
            self.state = self.switch_state(State.SETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, vertical)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK, as_thread=True)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_next = True
            log.info("Product stored at: " + str(f"({horizontal},{vertical})"))

    def retrieve_product(self, horizontal: int, vertical: int, as_thread=False):
        '''Retrieves a product from given position.

        :horizontal: horizontal coordinate
        :vertical: vertical coordinate
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.retrieve_product, args=(horizontal, vertical), name=self.name)
            self.thread.start()
            return
        
        log.info("Retrieve product from: " + str(f"({horizontal},{vertical})"))
        try:
            # move to given rack
            self.state = self.switch_state(State.MOVING_TO_RACK)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)
            self.move_to_position(horizontal, vertical)

            # get product from rack
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, self.POS_CB_VERTICAL - 100)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)

            # move to cb
            self.state = self.switch_state(State.MOVING_TO_CB)
            self.move_to_position(self.POS_CB_HORIZONTAL, self.POS_CB_VERTICAL - 100)

            # put product on cb
            self.state = self.switch_state(State.SETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, vertical)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK, as_thread=True)

            # move product to outside
            self.state = self.switch_state(State.CB_FWD)
            self.cb.run_to_stop_sensor("FWD", self.name + "_SENS_OUT")

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
            log.info("Retrieved product from: " + str(f"({horizontal},{vertical})"))


    def move_to_position(self, horizontal: int, vertical: int, as_thread=False):
        '''Moves Crane given coordinates, set a coordinate to -1 to not move that axis.

        :horizontal: horizontal coordinate
        :vertical: vertical coordinate
        :as_thread: Runs the function as a thread

        -> Panics if axes movements did not complete
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(horizontal, vertical), name=self.name)
            self.thread.start()
            return
        
        log.info("Moving Crane to position: " + str(f"({horizontal},{vertical})"))

        # get current position
        current_horizontal = self.encoder_hor.get_encoder_value()
        current_vertical = self.encoder_ver.get_encoder_value()
        

        # get motor directions
        dir_hor = "TO_RACK"
        dir_ver = "DOWN"
        if horizontal < current_horizontal:
            dir_hor = "TO_RACK"
        if vertical < current_vertical:
            dir_ver = "UP"

        
        # move to position
        self.move_axis(self.motor_hor, horizontal, current_horizontal, self.move_threshold_hor, dir_hor, self.encoder_hor, self.name + "_REF_SW_HORIZONTAL", as_thread=True)
        self.move_axis(self.motor_ver, vertical, current_vertical, self.move_threshold_ver, dir_ver, self.encoder_ver, self.name + "_REF_SW_VERTICAL", as_thread=True)

        # wait for end of each move
        if self.motor_hor.thread.is_alive():
            self.motor_hor.thread.join()
        if self.motor_ver.thread.is_alive():
            self.motor_ver.thread.join()

        log.info("Moved crane to: " + str(f"({horizontal},{vertical})"))

        
    def move_axis(self, motor: Actuator, trigger_value: int, current_value: int, move_threshold: int, direction: str, encoder: Sensor, ref_sw: str, timeout_in_s=10, as_thread=False):
        '''Moves one axis to the given trigger value.
        
        :motor: Motor object 
        :trigger_value: Encoder-Value at which the motor stops
        :current_value: Current Encoder-Value to determine if move is necessary
        :move_threshold: Value that has at min to be traveled to start the motor
        :direction: Motor direction, (everything after {NAME}_)
        :encoder: Sensor object
        :ref_sw: Reference Switch at which the motor stops if it runs to the encoder start 
        :timeout_in_s: Time after which an exception is raised
        :as_thread: Runs the function as a thread

        -> Panics if timeout is reached (no detection happened)
        '''
        # if trigger_value (position) is -1 do not move that axis
        if trigger_value == -1:
            return
        # if trigger value is 0 move to init position
        if trigger_value == 0:
            motor.run_to_encoder_start(direction, ref_sw, encoder, timeout_in_s, as_thread)
        # if trigger value is the same as the current value don't move
        elif abs(current_value - trigger_value) < move_threshold:
            log.info("Axis already at value: " + self.name + motor.type)
        # move to value
        else:
            motor.run_to_encoder_value(direction, encoder, trigger_value, timeout_in_s, as_thread)
  