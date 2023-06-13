'''This module controls the Warehouse, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.09"

import threading
from time import sleep
from enum import Enum
import json

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
    CB_BWD = 5
    CB_FWD = 6
    END = 100
    ERROR = 999

class ShelfPos(Enum):
    # [Horizontal, Vertical]
    SHELF_1_1 = [1540, 200]
    SHELF_1_2 = [1540, 900]
    SHELF_1_3 = [1540, 1650]
    SHELF_2_1 = [2675, 200]
    SHELF_2_2 = [2675, 900]
    SHELF_2_3 = [2675, 1650]
    SHELF_3_1 = [3840, 200]
    SHELF_3_2 = [3840, 900]
    SHELF_3_3 = [3840, 1650]

class Warehouse(Machine):
    '''Controls the Warehouse
    
    store_product(): Stores a product at given position.
    retrieve_product(): Retrieves a product from given position.
    move_to_position(): Moves Crane given coordinates.
    move_axis(): Moves one axis to the given trigger value.
    '''
    POS_CB_HORIZONTAL = 55
    POS_CB_VERTICAL = 1400

    JSON_FILE = "wh_content.json"
    color = "COLOR_UNKNOWN"


    def __init__(self, revpi, name: str):
        '''Initializes the Warehouse
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
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
        self.motor_loading = Actuator(self.revpi, self.name + "_ARM", type="loading")
        self.motor_hor = Actuator(self.revpi, self.name + "_CRANE", type="horizontal")
        self.motor_ver = Actuator(self.revpi, self.name + "_ARM", type="vertical")

        log.debug("Created Warehouse: " + self.name)


    def __del__(self):
        log.debug("Destroyed Warehouse: " + self.name)


    def init(self, to_end=False, as_thread=True):
        '''Move to init position.
        
        :to_end: set end_machine to True after completion of init
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(to_end, False), name=self.name)
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)
        log.info(f"Initializing {self.name}, moving to init position")
        try:
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)
            self.move_to_position(0, 0)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.stage += 1
            if to_end:
                self.end_machine = True


    def store_product(self, shelf: ShelfPos=None, as_thread=True):
        '''Stores a product at given position.

        :shelf: a position of a shelf defined in ShelfPos
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.store_product, args=(shelf, False), name=self.name)
            self.thread.start()
            return

        try:
            if Sensor(self.revpi, self.name + "_SENS_OUT").get_current_value() == False:
                raise(Exception("No Product to store found"))
            
            if shelf == None:
                # find empty shelf
                with open(Warehouse.JSON_FILE, "r") as fp:
                    json_obj = json.load(fp)
                for key, val in json_obj["contents"].items():
                    if val == "Empty":
                        for bay in ShelfPos:
                            if str(bay.name) == key:
                                shelf = bay
                                break
                        if shelf != None:
                            break

            
            horizontal = shelf.value[0]
            vertical = shelf.value[1]
            log.info(f"Store product at: {shelf.name}({horizontal},{vertical})")


            # move crane to cb
            self.state = self.switch_state(State.MOVING_TO_CB)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)
            self.move_to_position(self.POS_CB_HORIZONTAL, self.POS_CB_VERTICAL)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT, as_thread=True)

            # move product to inside
            sleep(2)
            self.state = self.switch_state(State.CB_FWD)
            self.cb.run_to_stop_sensor("FWD", self.name + "_SENS_IN", as_thread=False)

            # get product from cb
            self.motor_loading.join()
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.move_to_position(-1, self.POS_CB_VERTICAL - 100)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)

            # move crane to given rack
            self.state = self.switch_state(State.MOVING_TO_RACK)
            self.move_to_position(horizontal, vertical - 100)

            # store product in rack
            self.state = self.switch_state(State.SETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, vertical)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)
            
            # save Product to file
            with open(self.JSON_FILE, "r") as fp:
                json_obj = json.load(fp)
            json_obj["contents"][shelf.name] = self.color
            with open(self.JSON_FILE, "w") as fp:
                json.dump(json_obj, fp, indent=4)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.info("Product stored at: " + str(f"({horizontal},{vertical})"))
            self.state = self.switch_state(State.END)
            self.ready_for_next = True
            self.stage += 1


    def retrieve_product(self, shelf: ShelfPos=None, color: str=None, as_thread=True):
        '''Retrieves a product from given position.

        :shelf: a position of a shelf defined in ShelfPos
        :color: Color of the wanted Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier)
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.retrieve_product, args=(shelf, color, False), name=self.name)
            self.thread.start()
            return

        try:
            if shelf == None:
                # find wanted color
                with open(Warehouse.JSON_FILE, "r") as fp:
                    json_obj = json.load(fp)
                for key, val in json_obj["contents"].items():
                    if val == color:
                        for bay in ShelfPos:
                            if str(bay.name) == key:
                                shelf = bay
                                break
                        if shelf != None:
                            break
            
            horizontal = shelf.value[0]
            vertical = shelf.value[1]
            log.info(f"Retrieve product from: {shelf.name}({horizontal},{vertical})")

            # move to given rack
            self.state = self.switch_state(State.MOVING_TO_RACK)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)
            self.move_to_position(horizontal, vertical)

            # get product from rack
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, vertical - 100)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK)

            # move to cb
            self.state = self.switch_state(State.MOVING_TO_CB)
            self.move_to_position(self.POS_CB_HORIZONTAL, self.POS_CB_VERTICAL - 100)

            # put product on cb
            self.state = self.switch_state(State.SETTING_PRODUCT)
            self.motor_loading.run_to_sensor("FWD", self.REF_SW_ARM_FRONT)
            self.move_to_position(-1, self.POS_CB_VERTICAL)
            self.motor_loading.run_to_sensor("BWD", self.REF_SW_ARM_BACK, as_thread=True)

            # move product to outside
            self.state = self.switch_state(State.CB_BWD)
            self.cb.run_to_stop_sensor("BWD", self.name + "_SENS_OUT", as_thread=False)
            self.motor_loading.join()

            # save empty to file
            with open(self.JSON_FILE, "r") as fp:
                json_obj = json.load(fp)
            json_obj["contents"][shelf.name] = "Empty"
            with open(self.JSON_FILE, "w") as fp:
                json.dump(json_obj, fp, indent=4)


        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.info("Retrieved product from: " + str(f"({horizontal},{vertical})"))
            self.state = self.switch_state(State.END)
            self.ready_for_transport = True
            self.init(to_end=True, as_thread=True)


    def move_to_position(self, horizontal: int, vertical: int, as_thread=False):
        '''Moves Crane given coordinates, set a coordinate to -1 to not move that axis.

        :horizontal: horizontal coordinate
        :vertical: vertical coordinate
        :as_thread: Runs the function as a thread

        -> Panics if axes movements did not complete
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.move_to_position, args=(horizontal, vertical, False), name=self.name)
            self.thread.start()
            return

        log.info("Moving Crane to position: " + str(f"({horizontal},{vertical})"))

        # get current position
        current_horizontal = self.encoder_hor.get_current_value()
        current_vertical = self.encoder_ver.get_current_value()


        # get motor directions
        dir_hor = "TO_RACK"
        dir_ver = "DOWN"
        if horizontal <= current_horizontal:
            dir_hor = "TO_CB"
        if vertical <= current_vertical:
            dir_ver = "UP"


        # move to position
        self.motor_hor.move_axis(dir_hor, horizontal, current_horizontal, self.move_threshold_hor, self.encoder_hor, self.name + "_REF_SW_HORIZONTAL", timeout_in_s=20, as_thread=True)
        self.motor_ver.move_axis(dir_ver, vertical, current_vertical, self.move_threshold_ver, self.encoder_ver, self.name + "_REF_SW_VERTICAL", as_thread=True)

        # wait for end of each move
        self.motor_hor.join()
        self.motor_ver.join()

        log.info("Moved crane to: " + str(f"({horizontal},{vertical})"))
