'''This module controls the Warehouse, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.06.22"

import threading
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

# Positions in the Warehouse rack
POSITIONS: "list[list[tuple]]" = [
    [ # first column
        (1540, 200),
        (1540, 900),
        (1540, 1650)
    ],
    [ # second column
        (2675, 200),
        (2675, 900),
        (2675, 1650)
    ],
    [ # third column
        (3840, 200),
        (3840, 900),
        (3840, 1650)
    ]
]

class Warehouse(Machine):
    '''Controls the Warehouse
    
    store_product(): Stores a product at given position.
    retrieve_product(): Retrieves a product from given position.
    move_to_position(): Moves Crane given coordinates.
    move_axis(): Moves one axis to the given trigger value.
    '''
    __POS_CB_HORIZONTAL = 55
    __POS_CB_VERTICAL = 1450
    __MOVE_THRESHOLD_HOR = 40
    __MOVE_THRESHOLD_VER = 40
    __JSON_FILE = "wh_content.json"
    __color = "COLOR_UNKNOWN"
    __factory: str

    __ref_sw_arm_front: str = None
    __ref_sw_arm_back: str = None
    __cb: Conveyor = None
    __encoder_hor: Sensor = None
    __encoder_ver: Sensor = None
    __motor_loading: Actuator = None
    __motor_hor: Actuator = None
    __motor_ver: Actuator = None

    def __init__(self, revpi, name: str, factory: str):
        '''Initializes the Warehouse
        
        :revpi: RevPiModIO Object to control the motors and sensors
        :name: Exact name of the machine in PiCtory (everything bevor first '_')
        :factory: left / right to use the correct config
        '''
        super().__init__(revpi, name)
        self.__factory = factory

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


    def init(self, for_store=False, for_retrieve=False, to_end=False, as_thread=True):
        '''Move to init position.
        
        :to_cb: moves to cb after completion of init
        :to_end: set end_machine to True after completion of init
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(for_store, for_retrieve, to_end, False), name=self.name)
            self.thread.start()
            return
        
        self.state = self.switch_state(State.INIT)
        current_stage = self.stage
        try:
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            self.move_to_position(0, 0)

            if for_store:
                # get empty carrier if non is available
                if Sensor(self.revpi, self.name + "_SENS_OUT").get_current_value() == False:
                    self.retrieve_product(color="Carrier", as_thread=False)
                self.ready_for_next = True
                # move arm to cb
                self.state = self.switch_state(State.MOVING_TO_CB)
                Actuator(self.revpi, self.name + "_CB_BWD").run_for_time("", 0.5)
                self.move_to_position(self.__POS_CB_HORIZONTAL, self.__POS_CB_VERTICAL)
                self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            elif for_retrieve:
                # if carrier at cb, move it into storage
                if Sensor(self.revpi, self.name + "_SENS_OUT").get_current_value() == True:
                    # move arm to cb
                    self.state = self.switch_state(State.MOVING_TO_CB)
                    Actuator(self.revpi, self.name + "_CB_BWD").run_for_time("", 0.5)
                    self.move_to_position(self.__POS_CB_HORIZONTAL, self.__POS_CB_VERTICAL)
                    self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
                    self.store_product(color="Carrier", as_thread=False)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.warning()(f"{self.name}: Initialized")
            if to_end:
                self.state = self.switch_state(State.END)
                self.end_machine = True
            else:
                self.stage = current_stage + 1


    def store_product(self, position: POSITIONS=None, color: str=None, as_thread=True):
        '''Stores a product at given position.

        :position: a position of a shelf defined in POSITIONS
        :color: Color of the wanted Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier)
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.store_product, args=(position, color, False), name=self.name)
            self.thread.start()
            return

        color = color if color != None else self.__color

        try:
            if Sensor(self.revpi, self.name + "_SENS_OUT").get_current_value() == False:
                raise(Exception("No Product to store found"))
            
            if position == None:
                # find wanted color
                with open(Warehouse.__JSON_FILE, "r") as fp:
                    positions = json.load(fp)[self.__factory]

                # find the nearest empty bay
                for hor in range(3):
                    for ver in range(3):
                        if positions[hor][ver] == "Empty":
                            position = POSITIONS[hor][ver]
                            break
                    else:
                        continue
                    break
            
            horizontal = position[0]
            vertical = position[1]
            log.warning(f"{self.name} :Store {color}-product at position: [hor:{hor},ver:{ver}]; {position}")


            # move product to inside
            self.state = self.switch_state(State.CB_FWD)
            self.__cb.run_to_stop_sensor("FWD", self.name + "_SENS_IN", as_thread=False)

            # get product from cb
            self.state = self.switch_state(State.GETTING_PRODUCT)
            self.move_to_position(-1, self.__POS_CB_VERTICAL - 150)
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
            for hor in range(3):
                for ver in range(3):
                    if POSITIONS[ver][hor] == position:
                        break
                else:
                    continue
                break
            with open(Warehouse.__JSON_FILE, "r") as fp:
                json_obj = json.load(fp)
            json_obj[self.__factory][hor][ver] = color
            with open(self.__JSON_FILE, "w") as fp:
                json.dump(json_obj, fp, indent=4)

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.warning(f"{self.name} :{color}-product stored at position: [hor:{hor},ver:{ver}]; {position}")
            self.ready_for_transport = True
            self.stage += 1


    def retrieve_product(self, position: tuple=None, color: str=None, as_thread=True):
        '''Retrieves a product from given position.

        :position: a position of a shelf defined in POSITIONS
        :color: Color of the wanted Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier)
        :as_thread: Runs the function as a thread
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.retrieve_product, args=(position, color, False), name=self.name)
            self.thread.start()
            return

        color = color if color != None else self.__color

        try:
            if position == None:
                # find wanted color
                with open(Warehouse.__JSON_FILE, "r") as fp:
                    positions = json.load(fp)[self.__factory]

                # find the nearest empty bay
                for hor in range(3):
                    for ver in range(3):
                        if positions[hor][ver] == color:
                            position = POSITIONS[hor][ver]
                            break
                    else:
                        continue
                    break
            
            horizontal = position[0]
            vertical = position[1]
            log.warning(f"{self.name} :Retrieve {color}-product from position: [hor:{hor+1},ver:{ver+1}]; {position}")

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
            for hor in range(3):
                for ver in range(3):
                    if POSITIONS[ver][hor] == position:
                        break
                else:
                    continue
                break
            with open(Warehouse.__JSON_FILE, "r") as fp:
                json_obj = json.load(fp)
            json_obj[self.__factory][hor][ver] = "empty"
            with open(self.__JSON_FILE, "w") as fp:
                json.dump(json_obj, fp, indent=4)

            

        except Exception as error:
            self.state = self.switch_state(State.ERROR)
            self.error_exception_in_machine = True
            log.exception(error)
        else:
            log.warning(f"{self.name} :{color}-product retrieved from position: [hor:{hor+1},ver:{ver+1}]; {position}")
            self.ready_for_transport = True
            self.stage += 1


    def move_to_position(self, horizontal: int, vertical: int):
        '''Moves Crane given coordinates, set a coordinate to -1 to not move that axis.

        :horizontal: horizontal coordinate
        :vertical: vertical coordinate

        -> Panics if axes movements did not complete
        '''
        log.info("Moving Crane to position: " + str(f"(hor:{horizontal},ver:{vertical})"))

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
