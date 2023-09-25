# leftline module

Left line for MiniFactory project for machines:
Conveyor
PunchMach
Warehouse
VacRobot
GripRobot
IndexLine
MPStation

### *class* leftline.LeftLine(revpi, config: dict)

Bases: [`MainLine`](mainline.md#mainline.MainLine)

State loop and functions for left Factory.

Methodes:
: mainloop(): Switches between machines.
  <br/>
  ```
  run_
  ```
  <br/>
  …(): Calls the different modules.

#### WAREHOUSE_CONTENT_FILE

File path to the file that saves the warehouse inventory.

* **Type:**
  str

#### WAREHOUSE_CONTENT_FILE *= 'left_wh_content.json'*

#### mainloop()

Switches the line states.

#### run_cb1()

#### run_cb3()

#### run_cb4()

#### run_cb5()

#### run_gr1()

#### run_gr2()

#### run_gr3()

#### run_indx()

#### run_init()

#### run_mps()

#### run_pm()

#### run_wh_retrieve()

#### run_wh_store()

#### test()

### *class* leftline.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

NAME = [ID, Status, Used_by]

#### CB1 *= [11, Status.FREE, 'None']*

#### CB3_TO_CB4 *= [132, Status.FREE, 'None']*

#### CB3_TO_WH *= [131, Status.FREE, 'None']*

#### CB4 *= [14, Status.FREE, 'None']*

#### CB5 *= [15, Status.FREE, 'None']*

#### END *= [100, Status.FREE, 'None']*

#### ERROR *= [999, Status.FREE, 'None']*

#### GR1 *= [21, Status.FREE, 'None']*

#### GR2_CB1_TO_CB3 *= [221, Status.FREE, 'None']*

#### GR2_CB1_TO_PM *= [222, Status.FREE, 'None']*

#### GR2_PM_TO_CB3 *= [223, Status.FREE, 'None']*

#### GR3 *= [23, Status.FREE, 'None']*

#### INDX *= [4, Status.FREE, 'None']*

#### INIT *= [0, Status.FREE, 'None']*

#### MPS *= [5, Status.FREE, 'None']*

#### PM *= [6, Status.FREE, 'None']*

#### TEST *= [1000, Status.FREE, 'None']*

#### WAITING *= [99, Status.FREE, 'None']*

#### WH_RETRIEVE *= [82, Status.FREE, 'None']*

#### WH_STORE *= [81, Status.FREE, 'None']*
