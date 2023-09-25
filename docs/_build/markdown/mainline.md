# mainline module

Parent Class for production lines on MiniFactory project

### *class* mainline.MainLine(revpi, config: dict, states)

Bases: [`Machine`](machine.md#machine.Machine)

Controls the MiniFactory.

Methodes:
: update(): Updates the line
  line_config(): Config functionality
  mainloop(): Calls the different states
  switch_state(): Switches state to given state if not BLOCKED or RUNNING
  switch_status(): Switch status in states
  end(): Waits for any machines left running.

#### config

Config for the line.

* **Type:**
  dict

#### states

States from Subclass.

* **Type:**
  [State](conveyor.md#conveyor.State)

#### machines

All active machines.

* **Type:**
  dict

#### product_at

Name of machine where product is at.

* **Type:**
  bool

#### waiting_for_state

If line is waiting for machine, holds the state of that machine.

* **Type:**
  [State](conveyor.md#conveyor.State)

#### running

True if line is currently running.

* **Type:**
  bool

#### status_dict

Status of line.

* **Type:**
  dict

#### end()

Waits for any machines left running.

* **Returns:**
  True if all machine have endet else False.
* **Return type:**
  bool

#### get_machine(machine_name: str, machine_class, \*args)

Returns given machine, if not available initializes it.

* **Parameters:**
  * **machine_name** (*str*) – Name of machine that should be returned.
  * **machine_class** (*Mainloop*) – Class of the machine.
  * **\*args** – additional arguments passed to machine.
* **Returns:**
  machine object for given machine.
* **Return type:**
  [Machine](machine.md#machine.Machine)

#### line_config()

Config functionality.

* **Returns:**
  False if error occurred else returns True.

#### mainloop()

Abstract function should never be called

#### switch_state(state, wait=False)

Switch to given state and save state start time.

* **Parameters:**
  * **state** ([*State*](conveyor.md#conveyor.State)) – State Enum to switch to.
  * **wait** (*bool*) – Calls for input bevor switching.

#### switch_status(state_name, status: [Status](#mainline.Status))

Switch status in states, if name switches all to a machine belonging states.

* **Parameters:**
  * **state** ([*State*](conveyor.md#conveyor.State) *|* *str*) – Can be a State Enum or a string of to switching state.
  * **status** ([*Status*](#mainline.Status)) – Status that the state should be switched to.

#### update(run: bool)

Updates the line.

* **Parameters:**
  **run** – Only run the line if True.

### *class* mainline.Status(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### BLOCKED *= 3*

#### FREE *= 1*

#### NONE *= 0*

#### RUNNING *= 2*

#### WAITING *= 4*
