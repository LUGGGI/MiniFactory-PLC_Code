# robot_3d module

This module controls the 3D Robots, it inherits from Machine

### *exception* robot_3d.GetProductError

Bases: `SystemError`

Robot could not grip Product.

### *class* robot_3d.Position(rotation: int, horizontal: int, vertical: int)

Bases: `object`

Holds a int value for each axis.

#### rotation

Rotation position.

* **Type:**
  int

#### horizontal

Horizontal position.

* **Type:**
  int

#### vertical

Vertical position.

* **Type:**
  int

### *class* robot_3d.Robot3D(revpi, name: str, line_name: str, moving_position: [Position](#robot_3d.Position))

Bases: [`Machine`](machine.md#machine.Machine)

Controls the 3D Robot.

Methodes:
: init(): Move to init position.
  move_to_position(): Moves to given position.
  move_all_axes(): Makes linear move to give position.

#### \_\_MOVE_THRESHOLD_ROT

Only moves the rotation axis if movement is more.

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

#### \_\_MAX_PICKUP_TRIES

Max tries the robot can use to pickup a product.

* **Type:**
  int

#### \_\_moving_position

Position where the axes should be to allow save moving.

* **Type:**
  [Position](#robot_3d.Position)

#### \_\_encoder_rot

Encoder for rotation axis.

* **Type:**
  [Sensor](sensor.md#sensor.Sensor)

#### \_\_encoder_hor

Encoder for horizontal axis.

* **Type:**
  [Sensor](sensor.md#sensor.Sensor)

#### \_\_encoder_ver

Encoder for vertical axis.

* **Type:**
  [Sensor](sensor.md#sensor.Sensor)

#### pwm_rot

PWM name for rotation axis.

* **Type:**
  str

#### pwm_hor

PWM name for horizontal axis.

* **Type:**
  str

#### pwm_ver

PWM name for vertical axis.

* **Type:**
  str

#### \_\_motor_rot

Motor for rotation axis.

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

#### get_product(vertical_position: int, sensor: str = None, as_thread=True)

Moves to position without moving position, grips product and moves back up to original position.

* **Parameters:**
  * **vertical_position** (*int*) – Vertical value to move to to grip.
  * **sensor** (*str*) – Sensor that will be checked for detection while moving up.
  * **as_thread** (*bool*) – Runs the function as a thread.

#### grip(as_thread=True)

Grip product. Abstract function, see subclass.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

#### init(to_end=False, as_thread=True)

Move to init position.
:param to_end: If True ends machine after completion of init.
:type to_end: bool
:param as_thread: Runs the function as a thread.
:type as_thread: bool

#### move_to_position(position: [Position](#robot_3d.Position), ignore_moving_pos=False, as_thread=True)

Moves Robot to given position.

* **Parameters:**
  * **position** ([*Position*](#robot_3d.Position)) – to move to (rotation, horizontal, vertical): int.
  * **ignore_moving_pos** (*bool*) – If True robot won’t move to moving Position.
  * **as_thread** (*bool*) – Runs the function as a thread.

#### release(as_thread=True)

Release product. Abstract function, see subclass.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

#### reset_claw(as_thread=True)

Reset gripper. Abstract function, see subclass.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

### *class* robot_3d.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### END *= 100*

#### ERROR *= 999*

#### GET_PRODUCT *= 6*

#### GRIPPING *= 4*

#### INIT *= 0*

#### MOVING *= 2*

#### RELEASE *= 5*

#### TO_DESTINATION *= 3*

#### TO_MOVING_POS *= 1*
