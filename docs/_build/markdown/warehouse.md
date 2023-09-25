# warehouse module

This module controls the Warehouse, it inherits from Machine

### *class* warehouse.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### CB_BWD *= 5*

#### CB_FWD *= 6*

#### END *= 100*

#### ERROR *= 999*

#### GETTING_PRODUCT *= 3*

#### INIT *= 0*

#### MOVING_TO_CB *= 1*

#### MOVING_TO_RACK *= 2*

#### SETTING_PRODUCT *= 4*

### *class* warehouse.Warehouse(revpi, name: str, line_name: str, content_file: str)

Bases: [`Machine`](machine.md#machine.Machine)

Controls the Warehouse

Methodes:
: init(): Move to init Position
  store_product(): Stores a product at given position.
  retrieve_product(): Retrieves a product from given position.
  \_\_move_to_position(): Moves Crane given coordinates.

#### \_\_POS_CB_HORIZONTAL

Horizontal position of conveyor belt.

* **Type:**
  int

#### \_\_POS_CB_VERTICAL

Vertical position of conveyor belt.

* **Type:**
  int

#### \_\_MOVE_THRESHOLD_HOR

Only moves the horizontal axis if movement is more.

* **Type:**
  int

#### \_\_MOVE_THRESHOLD_VER

Only moves the vertical axis if movement is more.

* **Type:**
  int

#### \_\_content_file

File path to the file that saves the inventory.

* **Type:**
  str

#### ready_for_product

True if a carrier is at input for store.

* **Type:**
  bool

#### \_\_ref_sw_arm_front

Referenz switch name for arm in extended state.

* **Type:**
  str

#### \_\_ref_sw_arm_back

Referenz switch name for arm in retracted state.

* **Type:**
  str

#### \_\_cb

Conveyor object for in-/output conveyor.

* **Type:**
  [Conveyor](conveyor.md#conveyor.Conveyor)

#### \_\_encoder_hor

Encoder for horizontal axis.

* **Type:**
  [Sensor](sensor.md#sensor.Sensor)

#### \_\_encoder_ver

Encoder for vertical axis.

* **Type:**
  [Sensor](sensor.md#sensor.Sensor)

#### \_\_motor_loading

Motor for arm front-back axis.

* **Type:**
  [Actuator](actuator.md#actuator.Actuator)

#### \_\_motor_hor

Motor for horizontal axis.

* **Type:**
  [Actuator](actuator.md#actuator.Actuator)

#### \_\_motor_ver

Motor for vertical axis.

* **Type:**
  [Actuator](actuator.md#actuator.Actuator)

#### \_\_color

Color of product.

* **Type:**
  str

#### init(for_store=False, for_retrieve=False, to_end=False, as_thread=True)

Move to init position.

* **Parameters:**
  * **for_store** (*bool*) – Moves a carrier to input/output.
  * **for_retrieve** (*bool*) – Removes carrier from input/output.
  * **to_end** (*bool*) – If True ends machine after completion of init.
  * **as_thread** (*bool*) – Runs the function as a thread.

#### retrieve_product(position: [[1540, 200, 1540, 900, 1540, 1650], [2675, 200, 2675, 900, 2675, 1650], [3840, 200, 3840, 900, 3840, 1650]] = None, color: str = None, as_thread=True)

Retrieves a product from given position.

* **Parameters:**
  * **position** (*POSITIONS*) – Position of a shelf defined in POSITIONS, can be None.
  * **color** (*str*) – Color of the wanted Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier).
  * **as_thread** (*bool*) – Runs the function as a thread.

#### store_product(position: [[1540, 200, 1540, 900, 1540, 1650], [2675, 200, 2675, 900, 2675, 1650], [3840, 200, 3840, 900, 3840, 1650]] = None, color: str = None, as_thread=True)

Stores a product at given position.

* **Parameters:**
  * **position** (*POSITIONS*) – Position of a shelf defined in POSITIONS, can be None.
  * **color** (*str*) – Color of the Product (WHITE, RED, BLUE, COLOR_UNKNOWN, Carrier).
  * **as_thread** (*bool*) – Runs the function as a thread.
