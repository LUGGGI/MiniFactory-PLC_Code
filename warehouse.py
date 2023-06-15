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
    __POS_CB_HORIZONTAL = 55
    __POS_CB_VERTICAL = 1400
    __MOVE_THRESHOLD_HOR = 40
    __MOVE_THRESHOLD_VER = 40
    __JSON_FILE = "wh_content.json"
    color = "COLOR_UNKNOWN"

    __ref_sw_arm_front: str = None
    __ref_sw_arm_back: str = None
    __cb: Conveyor = None
    __encoder_hor: Sensor = None
    __encoder_ver: Sensor = None
    __motor_loading: Actuator = None
    __motor_hor: Actuator = None
    __motor_ver: Actuator = None

    def __init__(self, revpi, name: str):
        '''Initializes the Warehouse
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        '''
        super().__init__(revpi, name)

        self.__ref_sw_arm_front = self.name + "_REF_SW_ARM_FRONT"
        self.__ref_sw_arm_back = self.name + "_REF_SW_ARM_BACK"

        # get conveyor
        self.__cb = Conveyor(self.revpi, self.name + "_CB")

        # get encoder
        self.__encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_ENCODER")
        self.__encoder_ver = Sensor(self.revpi, self.name + "_VERTICAL_ENCODER")

        # get motors
        self.__motor_loading = Actuator(self.revpi, self.name + "_ARM", type="loading")
        self.__motor_hor = Actuator(self.revpi, self.name + "_CRANE", type="horizontal")
        self.__motor_ver = Actuator(self.revpi, self.name + "_ARM", type="vertical")

        log.debug("Created Warehouse: " + self.name)


    def __del__(self):
        log.debug("Destroyed Warehouse: " + self.name)


    def init(self, to_cb=False, to_end=False, as_thread=True):
        '''Move to init position.
        
        :to_cb: moves to cb after completion of init
        :to_end: set end_machine to True after completion of init
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(to_cb, to_end, False), name=self.name)
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)
        log.info(f"Initializing {self.name}, moving to init position")
        try:
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            self.move_to_position(0, 0)

            if to_cb:
                Actuator(self.revpi, self.name + "_CB_BWD").run_for_time("", 0.5)
                self.move_to_position(self.__POS_CB_HORIZONTAL, self.__POS_CB_VERTICAL)
                self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)

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
                with open(Warehouse.__JSON_FILE, "r") as fp:
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

            if self.state != State.INIT:
                # move crane to cb
                self.state = self.switch_state(State.MOVING_TO_CB)
                self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
                self.move_to_position(self.__POS_CB_HORIZONTAL, self.__POS_CB_VERTICAL)
                self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front, as_thread=False)

            # move product to inside
            self.state = self.switch_state(State.CB_FWD)
            self.__cb.run_to_stop_sensor("FWD", self.name + "_SENS_IN", as_thread=False)

            # get product from cb
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.move_to_position(-1, self.__POS_CB_VERTICAL - 100)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)

            # move crane to given rack
            self.state = self.switch_state(State.MOVING_TO_RACK)
            self.move_to_position(horizontal, vertical - 100)

            # store product in rack
            self.state = self.switch_state(State.SETTING_PRODUCT)
            self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            self.move_to_position(-1, vertical)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            
            # save Product to file
            with open(self.__JSON_FILE, "r") as fp:
                json_obj = json.load(fp)
            json_obj["contents"][shelf.name] = self.color
            with open(self.__JSON_FILE, "w") as fp:
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
                with open(Warehouse.__JSON_FILE, "r") as fp:
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
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            self.move_to_position(horizontal, vertical)

            # get product from rack
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            self.move_to_position(-1, vertical - 100)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)

            # move to cb
            self.state = self.switch_state(State.MOVING_TO_CB)
            self.move_to_position(0, self.__POS_CB_VERTICAL - 100)
            self.move_to_position(self.__POS_CB_HORIZONTAL, -1)

            # put product on cb
            self.state = self.switch_state(State.SETTING_PRODUCT)
            self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            self.move_to_position(-1, self.__POS_CB_VERTICAL)

            # move product to outside
            self.state = self.switch_state(State.CB_BWD)
            self.__cb.run_to_stop_sensor("BWD", self.name + "_SENS_OUT", stop_delay_in_ms=200, as_thread=False)

            # save empty to file
            with open(self.__JSON_FILE, "r") as fp:
                json_obj = json.load(fp)
            json_obj["contents"][shelf.name] = "Empty"
            with open(self.__JSON_FILE, "w") as fp:
                json.dump(json_obj, fp, indent=4)

            log.info("Retrieved product from: " + str(f"({horizontal},{vertical})"))
            self.ready_for_transport = True
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            self.init(to_end=True, as_thread=False)
            self.state = self.switch_state(State.END)


    def move_to_position(self, horizontal: int, vertical: int):
        '''Moves Crane given coordinates, set a coordinate to -1 to not move that axis.

        :horizontal: horizontal coordinate
        :vertical: vertical coordinate

        -> Panics if axes movements did not complete
        '''
        log.info("Moving Crane to position: " + str(f"({horizontal},{vertical})"))

        # get current position
        current_horizontal = self.__encoder_hor.get_current_value()
        current_vertical = self.__encoder_ver.get_current_value()


        # get motor directions
        dir_hor = "TO_RACK"
        dir_ver = "DOWN"
        if horizontal <= current_horizontal:
            dir_hor = "TO_CB"
        if vertical <= current_vertical:
            dir_ver = "UP"


        # move to position
        self.__motor_hor.move_axis(dir_hor, horizontal, current_horizontal, self.__MOVE_THRESHOLD_HOR, self.__encoder_hor, self.name + "_REF_SW_HORIZONTAL", timeout_in_s=20, as_thread=True)
        self.__motor_ver.move_axis(dir_ver, vertical, current_vertical, self.__MOVE_THRESHOLD_VER, self.__encoder_ver, self.name + "_REF_SW_VERTICAL", as_thread=True)

        # wait for end of each move
        self.__motor_hor.join()
        self.__motor_ver.join()

        log.info("Moved crane to: " + str(f"({horizontal},{vertical})"))
