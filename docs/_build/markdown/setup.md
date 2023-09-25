# setup module

Factory setup for MiniFactory project

### *class* setup.Setup(input_file, output_file, states, line_class)

Bases: `object`

Setup for Factory.

Methodes:
: run_factory(): Starts the factory, adds and updates the lines.
  \_\_update_factory(): Updates the factory and starts every line.
  \_\_save_status(): Puts the states, factory status and line status into output.

#### LOOP_TIME

How often a new iteration is started (in seconds).

* **Type:**
  int

#### revpi

RevPiModIO Object to control the motors and sensors.

* **Type:**
  RevPiModIO

#### states

All possible States of the line.

* **Type:**
  [State](conveyor.md#conveyor.State)

#### line_class

Class of the current line.

* **Type:**
  Mainline

#### exception

True if exception in factory.

* **Type:**
  bool

#### loop_start_time

Current loop start time.

* **Type:**
  float

#### last_config_update_time

Time of last config update.

* **Type:**
  float

#### lines

All Line objects currently active.

* **Type:**
  dict

#### exit_handler

Object for Exit Handler.

* **Type:**
  [ExitHandler](exit_handler.md#exit_handler.ExitHandler)

#### io_interface

Object for IO Interface.

* **Type:**
  [IOInterface](io_interface.md#io_interface.IOInterface)

#### LOOP_TIME *= 0.02*

#### run_factory()

Starts the factory, adds and updates the lines.
