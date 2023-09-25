# actuator module

This module handles communication with Actuators

### *class* actuator.Actuator(revpi: RevPiModIO, name: str, line_name: str, pwm: str = None, type: str = None)

Bases: `object`

Control for Actuators, can also call Sensors

Methodes:
: run_to_sensor(): Run Actuator until product is detected.
  run_for_time(): Run Actuator for certain amount of time.
  move_axis(): Moves an axis to the given trigger value.
  run_to_encoder_value(): Run Actuator until the trigger_value of encoder is reached.
  run_to_encoder_start(): Run Actuator to the encoder reference switch and resets the counter to 0.
  start(): Start actuator.
  stop(): Stop actuator.
  set_pwm(): Set PWM to percentage.
  join(): Joins the current thread and raises Exceptions.

#### \_\_ENCODER_TRIGGER_THRESHOLD

Range around trigger value where trigger happens for encoder.

* **Type:**
  int

#### \_\_COUNTER_TRIGGER_THRESHOLD

Range around trigger value where trigger happens for counter.

* **Type:**
  int

#### \_\_PWM_TRIGGER_THRESHOLD

Range around trigger value where trigger happens while actuator is slowed down.

* **Type:**
  int

#### \_\_PWM_WINDOW

Range around the trigger value where the actuator is slowed down from the start.

* **Type:**
  int

#### \_\_PWM_DURATION

Range around the trigger value where the actuator is slowed down.

* **Type:**
  int

#### \_\_revpi

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

#### \_\_pwm

Name of PWM-pin, Slows motor down, bevor reaching the value.

* **Type:**
  str

#### \_\_type

Specifier for motor name.

* **Type:**
  str

#### \_\_thread

Thread object if a function is called as thread.

* **Type:**
  Thread

#### exception

Holdes exception if exception was raised.

* **Type:**
  Exception

#### \_\_pwm_value

Value for pwm, the percentage of the speed.

* **Type:**
  int

#### log

Log object to print to log.

* **Type:**
  Logger

#### join()

Joins the current thread and raises Exceptions.

* **Raises:**
  **Exception** – Exceptions that a thrown in thread function.

#### move_axis(direction: str, trigger_value: int, current_value: int, move_threshold: int, encoder: [Sensor](sensor.md#sensor.Sensor), ref_sw: str, timeout_in_s=10, as_thread=False)

Moves an axis to the given trigger value.

* **Parameters:**
  * **direction** (*str*) – Actuator direction, (last part of whole name).
  * **trigger_value** (*int*) – Encoder-Value at which the motor stops.
  * **current_value** (*int*) – Current Encoder-Value to determine if move is necessary.
  * **move_threshold** (*int*) – Value that has at min to be traveled to start the motor.
  * **encoder** ([*Sensor*](sensor.md#sensor.Sensor)) – Sensor object for the used encoder.
  * **ref_sw** (*str*) – Reference Switch at which the motor stops if it runs to the encoder start.
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  * [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).
  * [**EncoderOverflowError**](sensor.md#sensor.EncoderOverflowError) – Encoder value negativ.
  * **ValueError** – Counter jumped values.

#### run_for_time(direction: str, wait_time_in_s: int, check_sensor: str = None, as_thread=False)

Run Actuator for certain amount of time.

* **Parameters:**
  * **direction** (*str*) – Actuator direction, (last part of whole name).
  * **wait_time_in_s** (*int*) – Time after which the actuator stops.
  * **check_sensor** (*str*) – If given, checks if detection occurred.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  [**NoDetectionError**](sensor.md#sensor.NoDetectionError) – No detection at check_sensor.

#### run_to_encoder_start(direction: str, ref_sw: str, encoder: [Sensor](sensor.md#sensor.Sensor), timeout_in_s=10, as_thread=False)

Run Actuator to the encoder reference switch and resets the encoder to 0.

* **Parameters:**
  * **direction** (*str*) – Actuator direction, (last part of whole name).
  * **ref_sw** (*str*) – Reference Switch at which the motor stops if it runs to the encoder start.
  * **encoder** ([*Sensor*](sensor.md#sensor.Sensor)) – Sensor object for the used encoder.
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).

#### run_to_encoder_value(direction: str, encoder: [Sensor](sensor.md#sensor.Sensor), trigger_value: int, timeout_in_s=20, as_thread=False)

Run Actuator until the trigger_value of encoder is reached.
:param direction: Actuator direction, (last part of whole name).
:type direction: str
:param encoder: Sensor object for the used encoder.
:type encoder: Sensor
:param trigger_value: Encoder-Value at which the motor stops.
:type trigger_value: int
:param timeout_in_s: Time after which an exception is raised.
:type timeout_in_s: int
:param as_thread: Runs the function as a thread.
:type as_thread: bool

* **Raises:**
  * [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).
  * [**EncoderOverflowError**](sensor.md#sensor.EncoderOverflowError) – Encoder value negativ.
  * **ValueError** – Counter jumped values.

#### run_to_sensor(direction: str, stop_sensor: str, stop_delay_in_ms=0, timeout_in_s=10, as_thread=False)

Run Actuator until product is detected by a Sensor, panics if nothing was detected.

* **Parameters:**
  * **direction** (*str*) – Actuator direction, (last part of whole name).
  * **stop_sensor** (*str*) – Stops Actuator if detection occurs at this Sensor.
  * **stop_delay_in_ms** (*int*) – Runs the Actuator this much longer after detection.
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
  * **as_thread** (*bool*) – Runs the function as a thread.
* **Raises:**
  [**SensorTimeoutError**](sensor.md#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).

#### set_pwm(percentage: int)

Set PWM value to percentage.

* **Parameters:**
  **percentage** (*int*) – speed of motor, (0..100) on is over 20.
* **Raises:**
  **ValueError** – Percentage out of range (0-100)

#### start(direction: str = '')

Start Actuator.

* **Parameters:**
  **direction** (*str*) – Actuator direction, (last part of whole name).

#### stop(direction: str = '')

Stop Actuator.

* **Parameters:**
  **direction** (*str*) – Actuator direction, (last part of whole name).
