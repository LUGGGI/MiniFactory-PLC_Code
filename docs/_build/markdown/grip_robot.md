# grip_robot module

This module controls the Gripper Robots, it inherits from Robot3D

### *class* grip_robot.GripRobot(revpi, name: str, line_name: str, moving_position: [Position](robot_3d.md#robot_3d.Position))

Bases: [`Robot3D`](robot_3d.md#robot_3d.Robot3D)

Controls the Gripper Robot.

Methodes:
: grip(): Grip Product.
  release(): Release Product.
  reset_claw(): Reset claw to init position.

#### GRIPPER_CLOSED

Value at which the gripper is closed.

* **Type:**
  int

#### GRIPPER_OPENED

Value at which the gripper is opened.

* **Type:**
  int

#### \_\_encoder_claw

Encoder (counter) for claw.

* **Type:**
  [Sensor](sensor.md#sensor.Sensor)

#### \_\_motor_claw

Motor for claw.

* **Type:**
  [Actuator](actuator.md#actuator.Actuator)

#### grip(as_thread=True)

Grip Product.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

#### release(as_thread=True)

Release product.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

#### reset_claw(as_thread=True)

Reset claw to init position.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.
