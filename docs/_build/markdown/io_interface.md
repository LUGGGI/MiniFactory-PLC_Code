# io_interface module

This module handles json config read and write

### *class* io_interface.IOInterface(input_file, output_file, states)

Bases: `object`

Handels json config read and program status update.

Methodes:
: update_configs_with_input(): Reads input file and appends the new configs to the configs list.
  \_\_check_if_config_already_exists(): Returns True if the given config already exist.
  update_output(): Update program status.

#### \_\_input_file

Config json file where the lines are configured.

* **Type:**
  str

#### \_\_output_file

Json file where the states are logged.

* **Type:**
  str

#### \_\_states

Possible States of line.

* **Type:**
  [State](conveyor.md#conveyor.State)

#### input_dict

Current input.

* **Type:**
  dict

#### new_configs

New line configs.

* **Type:**
  list

#### factory_run

If False the factory stops.

* **Type:**
  bool

#### factory_end

If False than the factory will not end if every line is finished.

* **Type:**
  bool

#### \_\_output_dict

Current output.

* **Type:**
  dict

#### \_\_update_num

Counts the number of output updates.

* **Type:**
  inz

#### update_configs_with_input()

Reads input file and appends the new configs to the configs list.

#### update_output(main_states: list, factory_status: dict, lines: dict)

Update program status.

* **Parameters:**
  * **main_states** (*list*) – Possible States of line.
  * **factory_status** (*dict*) – Status of whole factory.
  * **lines** (*dict*) – Status data for all machines in all lines.
