# index_line module

This module controls the Indexed Line with two Machining Stations (Mill and Drill), it inherits from machine

### *class* index_line.IndexLine(revpi, name: str, line_name: str)

Bases: [`Machine`](machine.md#machine.Machine)

Controls the Index Line.

Methodes:
: run(): Runs the Index Line routine.

#### \_\_TIME_MILLING

Time that the mill should be active.

* **Type:**
  int

#### \_\_TIME_DRILLING

Time that the drill should be active.

* **Type:**
  int

#### start_next_machine

Is set to True if next machine should be started.

* **Type:**
  bool

#### run(with_mill=False, with_drill=False, as_thread=True)

Runs the Index Line routine.

* **Parameters:**
  * **with_mill** (*bool*) – Product goes through mill.
  * **with_drill** (*bool*) – Product goes through drill.
  * **as_thread** (*bool*) – Runs the function as a thread.

### *class* index_line.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### DRILLING *= 4*

#### END *= 100*

#### ERROR *= 999*

#### MILLING *= 2*

#### START *= 0*

#### TO_DRILL *= 3*

#### TO_MILL *= 1*

#### TO_OUT *= 5*
