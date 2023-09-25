# vac_robot module

This module controls the Vacuum Robot, it inherits from Robot3D

### *class* vac_robot.VacRobot(revpi, name: str, line_name: str, moving_position=<robot_3d.Position object>)

Bases: [`Robot3D`](robot_3d.md#robot_3d.Robot3D)

Controls the Vacuum Robot

Methodes:
: grip(): Grip Product.
  release(): Release Product.

#### \_\_compressor

Compressor for vacuum gripper.

* **Type:**
  [Actuator](actuator.md#actuator.Actuator)

#### \_\_valve

valve for vacuum gripper.

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
