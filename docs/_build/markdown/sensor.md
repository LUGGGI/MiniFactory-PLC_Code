# sensor module

This module handles communication with Sensors

### *exception* sensor.EncoderOverflowError

Bases: `ValueError`

Encoder had a ‘negativ’ value.

### *exception* sensor.NoDetectionError

Bases: `ValueError`

No detection at Sensor.

### *class* sensor.Sensor(revpi: RevPiModIO, name: str, line_name: str, type: [SensorType](#sensor.SensorType) = None)

Bases: `object`

Control-methods for Senors.

Methodes:
: get_current_value(): Returns the current value of the sensor.
  start_monitor(): Start monitoring sensor for detection.
  remove_monitor(): Stop monitoring sensor.
  is_detected(): Returns True if product was detected. If True removes monitor.
  wait_for_detect(): Waits for detection at sensor.
  wait_for_encoder(): Waits for the encoder/counter to reach the trigger_value.
  reset_encoder(): Resets the encoder or counter to 0.

#### CYCLE_TIME

how often encoder/counter ar checked for new values.

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

#### type

Type of the sensor.

* **Type:**
  [SensorType](#sensor.SensorType)

#### counter_offset

Offset for counter so that counter can be used like encoder.

* **Type:**
  int

#### log

Log object to print to log.

* **Type:**
  Logger

#### CYCLE_TIME *= 0.005*

#### get_current_value()

Get the current value of the sensor.

* **Returns:**
  Value depending on SensorType.
  True if detection at LIGHT_BARRIER or REF_SWITCH.
  Int value of ENCODER or COUNTER.

#### is_detected(edge=33)

Check if product was detected. If True removes monitor.

* **Parameters:**
  **edge** – trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).
* **Returns:**
  True if product was detected, else false.

#### remove_monitor(edge=33)

Stop monitoring sensor.

* **Parameters:**
  **edge** – trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).

#### reset_encoder()

Resets the encoder or counter to 0.

* **Raises:**
  **TimeoutError** – Encoder/counter could not be reset in time”)

#### start_monitor(edge=33)

Start monitoring sensor for detection.

* **Parameters:**
  **edge** – trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).

#### wait_for_detect(edge=33, timeout_in_s=10)

Waits for detection at sensor.

* **Parameters:**
  * **edge** – trigger edge of the sensor, can be BOTH, RAISING, FALLING (from revpimodio2).
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
* **Raises:**
  [**SensorTimeoutError**](#sensor.SensorTimeoutError) – Timeout is reached (no detection happened)

#### wait_for_encoder(trigger_value: int, trigger_threshold: int, timeout_in_s=10)

Waits for the encoder/counter to reach the trigger_value.

* **Parameters:**
  * **trigger_value** (*int*) – The value the motor would end up if it started from reverence switch.
  * **trigger_threshold** (*int*) – The value around the trigger_value where a trigger can happen.
  * **timeout_in_s** (*int*) – Time after which an exception is raised.
* **Returns:**
  Reached encoder_value
* **Raises:**
  * [**SensorTimeoutError**](#sensor.SensorTimeoutError) – Timeout is reached (no detection happened).
  * [**EncoderOverflowError**](#sensor.EncoderOverflowError) – Encoder value negativ.
  * **ValueError** – Counter jumped values.

### *exception* sensor.SensorTimeoutError

Bases: `TimeoutError`

Timeout occurred while waiting for Sensor.

### *class* sensor.SensorType(value, names=None, \*, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: `Enum`

#### COUNTER *= 3*

#### ENCODER *= 2*

#### LIGHT_BARRIER *= 0*

#### REF_SWITCH *= 1*

### sensor.event_det_at_sensor(io_name, \_\_)

Set detection to True
