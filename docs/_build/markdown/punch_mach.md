# punch_mach module

This module controls the Punching Line with the connected Conveyor, it inherits from Machine

### *class* punch_mach.PunchMach(revpi, name: str, line_name: str)

Bases: [`Machine`](machine.md#machine.Machine)

Controls the Punching Maschine.

Methodes:
: run(): Runs the Punching Maschine routine.

#### ready_for_transport

If True then the next machine can transport the product.

* **Type:**
  bool

#### run(out_stop_sensor: str, as_thread=True)

Runs the Punching Maschine routine.

* **Parameters:**
  * **out_stop_sensor** (*str*) – Sensor at which the cb stops when outputting.
  * **as_thread** (*bool*) – Runs the function as a thread.

### *class* punch_mach.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### CB_TO_OUT *= 3*

#### CB_TO_PUNCH *= 1*

#### END *= 100*

#### ERROR *= 999*

#### PUNCHING *= 2*

#### START *= 0*
