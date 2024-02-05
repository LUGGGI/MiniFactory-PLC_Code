'''This module controls the Warehouse, it inherits from Machine'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.12"

import threading
from enum import Enum
import json

from lib.logger import log
from lib.machine import Machine, MainState
from lib.sensor import Sensor, SensorTimeoutError, EncoderOverflowError
from lib.actuator import Actuator
from lib.conveyor import Conveyor

class State(Enum):
    INIT = 0
    MOVING_TO_CB = 1
    MOVING_TO_RACK = 2
    GETTING_PRODUCT = 3
    SETTING_PRODUCT = 4
    CB_BWD = 5
    CB_FWD = 6

# Positions in the Warehouse rack
POSITIONS: "list[list[tuple]]" = [
    [ # first column
        (1540, 200),
        (1540, 900),
        (1540, 1650)
    ],
    [ # second column
        (2700, 200),
        (2700, 900),
        (2700, 1650)
    ],
    [ # third column
        (3840, 200),
        (3840, 900),
        (3840, 1650)
    ]
]

class Warehouse(Machine):
    '''Controls the Warehouse'''
    '''
    Methodes:
        init(): Move to init Position
        store_product(): Stores a product at given position.
        retrieve_product(): Retrieves a product from given position.
        __move_to_position(): Moves Crane given coordinates.
    Attributes:
        __POS_CB_HORIZONTAL (int): Horizontal position of conveyor belt.
        __POS_CB_VERTICAL (int): Vertical position of conveyor belt.
        __MOVE_THRESHOLD_HOR (int): Only moves the horizontal axis if movement is more.
        __MOVE_THRESHOLD_VER (int): Only moves the vertical axis if movement is more.
        __LIFT_VALUE_RACK (int): Value that the arm lifts a Carrier at rack.
        __LIFT_VALUE_CB (int): Value that the arm lifts a Carrier at cb.
        __content_file (str): File path to the file that saves the inventory.
        ready_for_product (bool): True if a carrier is at input for store.
        __ref_sw_arm_front (str): Referenz switch name for arm in extended state.
        __ref_sw_arm_back (str): Referenz switch name for arm in retracted state.
        __cb (Conveyor): Conveyor object for in-/output conveyor.
        __encoder_hor (Sensor): Encoder for horizontal axis.
        __encoder_ver (Sensor): Encoder for vertical axis.
        __motor_loading (Actuator): Motor for arm front-back axis.
        __motor_hor (Actuator): Motor for horizontal axis.
        __motor_ver (Actuator): Motor for vertical axis.
        __color (str): Color of product.
    '''
    __POS_CB_HORIZONTAL = 85
    __POS_CB_VERTICAL = 1450
    __MOVE_THRESHOLD_HOR = 40
    __MOVE_THRESHOLD_VER = 40
    __LIFT_VALUE_RACK = 150
    __LIFT_VALUE_CB = 150

    def __init__(self, revpi, name: str, line_name: str, content_file: str):
        '''Initializes the Warehouse.
        
        Args:
            revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
            name (str): Exact name of the machine in PiCtory (everything before first '_').
            line_name (str): Name of current line.
            content_file (str): File path to the file that saves the inventory.
        '''
        super().__init__(revpi, name, line_name)

        self.__content_file = content_file
        self.ready_for_product = False

        self.__ref_sw_arm_front = self.name + "_REF_SW_ARM_FRONT"
        self.__ref_sw_arm_back = self.name + "_REF_SW_ARM_BACK"

        # get conveyor
        self.__cb = Conveyor(self.revpi, self.name + "_CB", self.line_name)

        # get encoder
        self.__encoder_hor = Sensor(self.revpi, self.name + "_HORIZONTAL_ENCODER", self.line_name)
        self.__encoder_ver = Sensor(self.revpi, self.name + "_VERTICAL_ENCODER", self.line_name)

        # get motors
        self.__motor_loading = Actuator(self.revpi, self.name + "_ARM", self.line_name, type="loading")
        self.__motor_hor = Actuator(self.revpi, self.name + "_CRANE", self.line_name, type="horizontal")
        self.__motor_ver = Actuator(self.revpi, self.name + "_ARM", self.line_name, type="vertical")

        self.__color = "COLOR_UNKNOWN"

        global log
        self.log = log.getChild(f"{self.line_name}(Ware)")

        self.log.debug(f"Created {type(self).__name__}: {self.name}")


    def init(self, for_store=False, for_retrieve=False, to_end=False, as_thread=True):
        '''Move to init position.
        
        Args:
            for_store (bool): Moves a carrier to input/output.
            for_retrieve (bool): Removes carrier from input/output.
            to_end (bool): If True ends machine after completion of init.
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.init, args=(for_store, for_retrieve, to_end, False), name=self.name)
            self.thread.start()
            return
        
        self.switch_state(State.INIT)
        current_position = self.position
        try:
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            self.__move_to_position(0, 0)

            if for_store:
                # get empty carrier if non is available
                if Sensor(self.revpi, self.name + "_SENS_OUT", self.line_name).get_current_value() == False:
                    self.retrieve_product(color="Carrier", as_thread=False)
                self.ready_for_product = True
                # move arm to cb
                self.switch_state(State.MOVING_TO_CB)
                Actuator(self.revpi, self.name + "_CB_BWD", self.line_name).run_for_time("", 0.5)
                self.__move_to_position(self.__POS_CB_HORIZONTAL, self.__POS_CB_VERTICAL)
                self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            elif for_retrieve:
                # if carrier at cb, move it into storage
                if Sensor(self.revpi, self.name + "_SENS_OUT", self.line_name).get_current_value() == True:
                    # move arm to cb
                    self.switch_state(State.MOVING_TO_CB)
                    Actuator(self.revpi, self.name + "_CB_BWD", self.line_name).run_for_time("", 0.5)
                    self.__move_to_position(self.__POS_CB_HORIZONTAL, self.__POS_CB_VERTICAL)
                    self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
                    self.store_product(color="Carrier", as_thread=False)

        except (SensorTimeoutError, ValueError, EncoderOverflowError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            if to_end:
                self.switch_state(MainState.END)
            else:
                self.log.warning(f"{self.name}: Initialized")
                self.position = current_position + 1


    def store_product(self, position: POSITIONS=None, color: str=None, as_thread=True):
        '''Stores a product at given position.

        Args:
            position (POSITIONS): Position of a shelf defined in POSITIONS, can be None.
            color (str): Color of the Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier).
            as_thread (bool): Runs the function as a thread.
        '''
        # call this function again as a thread
        if as_thread:
            self.thread = threading.Thread(target=self.store_product, args=(position, color, False), name=self.name)
            self.thread.start()
            return

        color = color if color != None else self.__color

        try:
            if Sensor(self.revpi, self.name + "_SENS_OUT", self.line_name).get_current_value() == False:
                raise(Exception("No Product to store found"))
            
            if position == None:
                # find Empty bay
                with open(self.__content_file, "r") as fp:
                    positions = json.load(fp)["content"]

                # find the nearest empty bay
                for hor in range(3):
                    for ver in range(3):
                        if positions[hor][ver] == "Empty":
                            position = POSITIONS[hor][ver]
                            break
                    else:
                        continue
                    break
                else:
                    raise LookupError(f"{self.name}: No empty spaces left.")
            
            horizontal = position[0]
            vertical = position[1]
            self.log.warning(f"{self.name} :Store {color}-product at position: [hor:{hor},ver:{ver}]; {position}")


            # move product to inside
            self.switch_state(State.CB_FWD)
            self.__cb.run_to_stop_sensor("FWD", self.name + "_SENS_IN", as_thread=False)

            # get product from cb
            self.switch_state(State.GETTING_PRODUCT)
            self.__move_to_position(-1, self.__POS_CB_VERTICAL - self.__LIFT_VALUE_CB)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)

            # move crane to given rack
            self.switch_state(State.MOVING_TO_RACK)
            self.__move_to_position(horizontal, vertical - self.__LIFT_VALUE_RACK)

            # store product in rack
            self.switch_state(State.SETTING_PRODUCT)
            self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            self.__move_to_position(-1, vertical)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            
            # save Product to file
            for hor in range(3):
                for ver in range(3):
                    if POSITIONS[hor][ver] == position:
                        break
                else:
                    continue
                break
            with open(self.__content_file, "r") as fp:
                json_obj = json.load(fp)
            json_obj["content"][hor][ver] = color
            with open(self.__content_file, "w") as fp:
                json.dump(json_obj, fp, indent=4)

        except (SensorTimeoutError, ValueError, EncoderOverflowError, LookupError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.log.warning(f"{self.name} :{color}-product stored at position: [hor:{hor},ver:{ver}]; {position}")
            self.position += 1


    def retrieve_product(self, position: POSITIONS=None, color: str=None, as_thread=True):
        '''Retrieves a product from given position.

        Args:
            position (POSITIONS): Position of a shelf defined in POSITIONS, can be None.
            color (str): Color of the wanted Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier).
            as_thread (bool): Runs the function as a thread.
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
                with open(self.__content_file, "r") as fp:
                    positions = json.load(fp)["content"]

                # find the nearest empty bay
                for hor in range(3):
                    for ver in range(3):
                        if positions[hor][ver] == color:
                            position = POSITIONS[hor][ver]
                            break
                    else:
                        continue
                    break
                else:
                    raise LookupError(f"{self.name}: Color {color} not found.")
            
            horizontal = position[0]
            vertical = position[1]
            self.log.warning(f"{self.name} :Retrieve {color}-product from position: [hor:{hor+1},ver:{ver+1}]; {position}")

            # move to given rack
            self.switch_state(State.MOVING_TO_RACK)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)
            self.__move_to_position(horizontal, vertical)

            # get product from rack
            self.switch_state(State.GETTING_PRODUCT)
            self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            self.__move_to_position(-1, vertical - self.__LIFT_VALUE_RACK)
            self.__motor_loading.run_to_sensor("BWD", self.__ref_sw_arm_back)

            # move to cb
            self.switch_state(State.MOVING_TO_CB)
            self.__move_to_position(0, self.__POS_CB_VERTICAL - self.__LIFT_VALUE_CB)
            self.__move_to_position(self.__POS_CB_HORIZONTAL, -1)

            # put product on cb
            self.switch_state(State.SETTING_PRODUCT)
            self.__motor_loading.run_to_sensor("FWD", self.__ref_sw_arm_front)
            self.__move_to_position(-1, self.__POS_CB_VERTICAL)

            # move product to outside
            self.switch_state(State.CB_BWD)
            self.__cb.run_to_stop_sensor("BWD", self.name + "_SENS_OUT", stop_delay_in_ms=200, as_thread=False)

            # save "empty" to file
            for hor in range(3):
                for ver in range(3):
                    if POSITIONS[hor][ver] == position:
                        break
                else:
                    continue
                break
            with open(self.__content_file, "r") as fp:
                json_obj = json.load(fp)
            json_obj["content"][hor][ver] = "Empty"
            with open(self.__content_file, "w") as fp:
                json.dump(json_obj, fp, indent=4)
            
        except (SensorTimeoutError, ValueError, EncoderOverflowError, LookupError) as error:
            self.problem_handler(error)
        except Exception as error:
            self.error_handler(error)
        else:
            self.log.warning(f"{self.name} :{color}-product retrieved from position: [hor:{hor+1},ver:{ver+1}]; {position}")
            self.position += 1


    def __move_to_position(self, horizontal: int, vertical: int):
        '''Moves Crane given coordinates, set a coordinate to -1 to not move that axis.

        Args:
            horizontal (int): Horizontal coordinate to move to.
            vertical (int): Vertical coordinate to move to.

        Raises:
            SensorTimeoutError: Timeout is reached (no detection happened).
            EncoderOverflowError: Encoder value negativ.
            ValueError: Counter jumped values.
        '''
        self.log.info("Moving Crane to position: " + str(f"(hor:{horizontal},ver:{vertical})"))

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

        self.log.info("Moved crane to: " + str(f"({horizontal},{vertical})"))
