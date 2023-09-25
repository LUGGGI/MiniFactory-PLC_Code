# machine module

Parent class for all machine modules

### *class* machine.Machine(revpi: RevPiModIO, name: str, line_name: str)

Bases: `object`

Parent class for all machine modules.

Methodes:
: get_run_time(): Get run time of machine.
  get_state_time(): Get run time of current state.
  switch_state(): Switch to given state.
  is_position(): Returns True if no thread is running and given position is current position.

#### revpi

RevPiModIO Object to control the motors and sensors.

* **Type:**
  RevPiModIO

#### name

Exact name of the sensor in PiCtory (everything bevor first ‘_’).

* **Type:**
  str

#### line_name

Name of current line.

* **Type:**
  str

#### thread

Thread object if a function is called as thread.

* **Type:**
  Thread

#### \_\_time_start

Time of machine start.

* **Type:**
  float

#### \_\_state_time_start

Time of current state start.

* **Type:**
  float

#### end_machine

True if machine should end.

* **Type:**
  bool

#### error_exception_in_machine

True if exception in machine.

* **Type:**
  bool

#### problem_in_machine

True if problem in machine.

* **Type:**
  bool

#### position

Counts up the positions of the machine.

* **Type:**
  int

#### state

Current state of machine.

* **Type:**
  [State](conveyor.md#conveyor.State)

#### log

Log object to print to log.

* **Type:**
  Logger

#### get_run_time()

Get run time of machine in seconds since creation of Machine.

* **Returns:**
  Run time of machine.
* **Return type:**
  int

#### get_state_time()

Get run time of state in seconds since switch.

* **Returns:**
  Run time of state.
* **Return type:**
  int

#### get_status_dict()

Returns a dictionary with the machine status.

* **Returns:**
  Status dictionary
* **Return type:**
  dict

#### is_position(postion: int)

Returns True if no thread is running and given position is current position.

* **Parameters:**
  **position** (*int*) – position at which it should return True.
* **Returns:**
  True if no thread is running and at position.
* **Return type:**
  bool

#### switch_state(state, wait=False)

Switch to given state and save state start time.

* **Parameters:**
  * **state** ([*State*](conveyor.md#conveyor.State)) – State Enum to switch to.
  * **wait** (*bool*) – Waits for input bevor switching.
