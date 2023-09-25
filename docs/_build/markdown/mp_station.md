# mp_station module

This module controls the Multi Purpose Station, it inherits from Machine

### *class* mp_station.MPStation(revpi, name: str, line_name: str)

Bases: [`Machine`](machine.md#machine.Machine)

Controls the Multi Purpose Station.

Methodes:
: init(): Move to init position.
  run(): Runs the Multi Purpose Station routine.
  run_to_out(): Runs the Conveyor to move the product out.

#### \_\_TIME_OVEN

Time that the oven should be active.

* **Type:**
  int

#### \_\_TIME_SAW

Time that the saw should be active.

* **Type:**
  int

#### table

Actuator object for the table.

* **Type:**
  [Actuator](actuator.md#actuator.Actuator)

#### init(as_thread=True)

Move to init position.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

#### run(with_oven=True, with_saw=False, as_thread=True)

Runs the Multi Purpose Station routine.

* **Parameters:**
  * **with_oven** (*bool*) – Product goes through oven.
  * **with_saw** (*bool*) – Product goes through saw.
  * **as_thread** (*bool*) – Runs the function as a thread.

#### run_to_out(as_thread=True)

Runs the Conveyor to move the product out.

* **Parameters:**
  **as_thread** (*bool*) – Runs the function as a thread.

### *class* mp_station.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### CB *= 7*

#### END *= 100*

#### ERROR *= 999*

#### INIT *= 0*

#### OVEN *= 2*

#### SAWING *= 5*

#### START *= 1*

#### TO_CB *= 6*

#### TO_SAW *= 4*

#### TO_TABLE *= 3*
