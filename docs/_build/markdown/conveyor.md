# conveyor module

This module controls a Conveyor, it inherits from Machine

### *class* conveyor.Conveyor(revpi, name: str, line_name: str)

Bases: [`Machine`](machine.md#machine.Machine)

Controls a conveyor. If conveyor isn’t run with end_machine=True, the flag has to be set manually.

Methodes:
: run_to_stop_sensor(): Runs the Conveyor until the product has reached the stop sensor
  run_to_counter_value(): Runs the Conveyor until the trigger_value of encoder is reached

#### exception

Holds exception if exception was raised.

* **Type:**
  Exception

#### end_conveyor()

Ends conveyor.

#### join()

Joins the current thread and reraise Exceptions.

* **Raises:**
  **Exception** – Exceptions that a thrown in thread function.

#### run_for_time(direction: str, wait_time_in_s: int, check_sensor: str = None, end_machine=False, as_thread=True)

Runs the Conveyor for the given time, can check for sensor detection.

* **Parameters:**
  * **direction** (*str*) – Actuator direction, (last part of whole name).
  * **wait_time_in_s** (*int*) – Time after which the actuator stops.
  * **check_sensor** (*str*) – If given, checks if detection occurred.
  * **end_machine** (*bool*) – Ends the machine if this function completes, set to false to keep machine.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  * **Only if called from other Machine.** – 
  * [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).
  * [**EncoderOverflowError**](sensor.md#sensor.EncoderOverflowError) – Encoder value negativ.
  * **ValueError** – Counter jumped values.

#### run_to_counter_value(direction: str, counter: str, trigger_value: int, timeout_in_s=10, end_machine=False, as_thread=True)

Runs the Conveyor until the trigger_value of encoder is reached.

* **Parameters:**
  * **direction** (*str*) – Actuator direction, (last part of whole name).
  * **counter** (*str*) – Counter sensor that is checked with trigger_value.
  * **trigger_value** (*int*) – Value at which to stop Conveyor.
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
  * **end_machine** (*bool*) – Ends the machine if this function completes, set to false to keep machine.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  * **Only if called from other Machine.** – 
  * [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).
  * [**EncoderOverflowError**](sensor.md#sensor.EncoderOverflowError) – Encoder value negativ.
  * **ValueError** – Counter jumped values.

#### run_to_stop_sensor(direction: str, stop_sensor: str, start_sensor: str = None, stop_delay_in_ms=0, timeout_in_s=10, end_machine=False, as_thread=True)

Runs the Conveyor until the product has reached the stop sensor.

* **Parameters:**
  * **direction** (*str*) – Conveyor direction, (last part of whole name).
  * **stop_sensor** (*str*) – Stops Conveyor if detection occurs at this Sensor.
  * **start_sensor** (*str*) – Waits with starting until detection occurs at Sensor.
  * **stop_delay_in_ms** (*int*) – Runs for given ms after detection of stop_sensor.
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
  * **end_machine** (*bool*) – Ends the machine if this function completes, set to false to keep machine.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  * **Only if called from other Machine.** – 
  * [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).

### *class* conveyor.State(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### END *= 100*

#### ERROR *= 999*

#### RUN *= 1*

#### WAIT *= 0*
