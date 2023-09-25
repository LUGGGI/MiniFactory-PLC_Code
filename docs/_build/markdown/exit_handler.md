# exit_handler module

This handles exit/stop of factory

### *class* exit_handler.ExitHandler(revpi: RevPiModIO)

Bases: `object`

Stops the factory, and handles CTRL+C.

Methodes:
: stop_factory: Disables the API for factory and stops all Actuators.

#### revpi

RevPiModIO Object to control the motors and sensors.

* **Type:**
  RevPiModIO

#### was_called

Is set to true if exit handler was called.

* **Type:**
  bool

#### stop_factory(\*\_)

Disables the API for factory and stops all Actuators.
