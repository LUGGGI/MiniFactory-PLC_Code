# sort_line module

This module controls the Sorting Line, it inherits from machine

### *class* sort_line.SortLine(revpi, name: str, line_name: str)

Bases: [`Machine`](machine.md#machine.Machine)

Controls the Sorting Line

Methodes:
: run(): Runs the Sorting Line routine.

#### color

Color of product.

* **Type:**
  str

#### start_next_machine

Is set to True if next machine should be started.

* **Type:**
  bool

#### run(color: str = None, as_thread=True)

Runs the Sorting Line routine.

* **Parameters:**
  * **color** (*str*) – Color of product.
  * **as_thread** (*bool*) – Runs the function as a thread.

### *class* sort_line.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### COLOR_SENSING *= 1*

#### END *= 100*

#### ERROR *= 999*

#### INTO_BAY *= 3*

#### SORTING *= 2*

#### START *= 0*
