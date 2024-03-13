# Overview of the messages the factory sends and receivees

A Topic for the factory is build out of 3 Parts:

* Topic start is is `MiniFactory/Right/Factory` or `MiniFactory/Left/Factory`
* Subject for example `LineConfig` or `MachineStatus`
* Category can be:
  * `Set` Command to the factory (set a config or give a command)
  * `Get` Request data for the subject from the factory
  * `Data` Data send by the factory
* Example for topic are:
  * `MiniFactory/Right/Factory/LineConfig/Set`
  * `MiniFactory/Right/Factory/WHContent/Get`
  * `MiniFactory/Right/Factory/MachineStatus/Data`

All messages are json strings

## Set Messages

Category is `Set`

| Subject        | Explanation                                        |
| -------------- | -------------------------------------------------- |
| LineConfig     | Set or change a production line                    |
| FactoryConfig  | Set factory wide configs                           |
| FactoryCommand | Command the factory (for example to start or stop) |
| WHContent      | Set the Warehouse content                          |

### LineConfig

Set or change a production line

```python
line_config = [
	{
        "name": "Line1", 	# Name of the line, can be any string
        "run": True,		# If False line will stop (or not start)
        "start_at": "start",	# Position where the Line starts can be "start", "storage", or any machine in short form ("CB1", "MPS"...)
        "end_at": "end",	# Position where the Line ends can be "end", "storage", or any machine in short form ("CB1", "MPS"...)
	"with_oven": True,
        "with_saw": True,
        "with_PM": True,	# with_... if uses the specific machine on the line, if missing or False the machine will be skipped
        "with_mill": True,
        "with_drill": True,
        "color": "BLUE",	# Set the color of the product, can be "WHITE", "RED", "BLUE", "COLOR_UNKNOWN"
        "restart": True,	# If True the line will restart at "start_at" when it reaches "end_at"
        "start_when": "Line0",	# Only starts the line when the configured line (here "Line0") has ended
	"start_int": True,	# Uses an internal position for "start" coincides with the "end_int" position
        "end_int": True,	# Uses an internal position for "end" coincides with the "start_int" position
    },
]
```

### FacotryConfig

Set factory wide configs

```python
factory_config = {
    "exit_if_end": True,		# If True the factory will stop if no line is running
}
```

### FactoryCommand

Command the factory

```python
factory_command = {
    "run": True,		# Factory only runs if set to True, if False the factory will halt at next possible time
    "stop": False,		# If True factory will stop immediately
}
```

### WHContent

Set the Warehouse content

* First array is the Column nearest to in and output station at warehouse

```python
wh_content = [
    [
        "WHITE",
        "RED",
        "BLUE"
    ],
    [
        "Carrier",
        "Carrier",
        "Empty"
    ],
    [
        "COLOR_UNKNOWN",
        "Empty",
        "Empty"
    ]
]
```


## Get and Data Messages

Get the data by sending an empty message top the topic with the wanted subject and `/Get` (for example `LineConfig/Get`)

Some data will also be send out it if changes

| Subject        | Explanation                                                                              |
| -------------- | ---------------------------------------------------------------------------------------- |
| LineConfig     | See all line configs currently active in the factory, format will be like in Set messages |
| FactoryConfig  | see Set messages                                                                         |
| FactoryCommand | see Set messages                                                                         |
| WHContent      | see Set messages                                                                         |
| MachineStatus  | Status of all Machines, includes the name of the line that is using it                   |
| LineStatus     | Status of the active Lines. Includes detailed status info and error messages             |
| FactoryStatus  | Status messages from factory, Can **not** be requested with `/Get`             |

### MachineStatus

Examples:

```python
{'GR1': ['RUNNING', 'Line1']}		# Line1 is using GR1
{'MPS': ['FREE', 'None']}		# No line is using MPS
{'CB1': ['PROBLEM', 'LineE1']}		# Line1E encountered a problem at CB1
```

### LineStatus

Examples:

```python
{'Line1': {'self': {'state': 'GR1', 'product_at': None}}}
	# Line1 is runnig GR1, product has not been picked up
{'Line1': {'self': {'state': 'GR1', 'product_at': 'GR1'}, 'GR1': {'status': 'GRIPPING'}, 'MPS': {'status': 'INIT'}}}
	# Line1 is GRIPPING with GR1 and INIT at MPS, product is now at GR1
{'LineE1': {'self': {'state': 'PROBLEM', 'product_at': 'CB1'}, 'CB1': {'status': 'PROBLEM', 'PROBLEM': 'SensorTimeoutError: CB1_SENS_END no detection in time'}}}
	# there was a PROBLEM in LineE1, the problem occurred in CB1 with the given message
```

### FactoryStatus

```python
{'line_added': {'name': 'Line1', 'run': True, 'start_at': 'start', 'end_at': 'end'}}
	# New line added, also includes its config
{'line_changed': {'name': 'Line1', 'run': True, 'start_at': 'start', 'end_at': 'storage'}}
	# Line has, also includes its config
{'line_started': {'name': 'Line1', 'at': 'GR1'}}
	# Line started, includes the machine where it started at
{'line_ended': {'name': 'Line1', 'at': 'END'}}
	# Line reached end position, include machine where it ended
{'line_stopped': 'Line1'}
  	# Line stopped
{"status": "Program started"}
	# Factory program started
{"status": "Program stopped"}
	# Factory program stopped
{'ERROR': "Error in line Line1w: ...."}
	# Fatal error that can't be recovered from, should never happen
```
