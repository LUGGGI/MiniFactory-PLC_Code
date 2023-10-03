.. MiniFactory documentation master file, created by
   sphinx-quickstart on Thu Sep 21 16:46:23 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=======================================
Doc for MiniFactory SPS-Control!
=======================================

This is the documentation for the MiniFactory PLC control.

=======================================
Structure
=======================================

Factory control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- :doc:`/setup` contains the control between the individual production lines.

Production line control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- In :doc:`/leftline` and :doc:`/rightline` is the specific code for each production line.
- In :doc:`/mainline` are the configuration functions for the production lines, :doc:`"...line" </rightline>` are subclasses of them.

Machine control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- :doc:`/sensor` and :doc:`/actuator` implement the API and provide various functions for handling the sensors/actuators. 
- The individual machine classes contain the specific control commands for the respective machine class.

Auxiliary modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- :doc:`/exit_handler` stops the machine on execution.
- :doc:`/io_interface` implements communication (currently in files).
- :doc:`/logger` provides the possibility to write to the log.

\
\

=======================================
Control Production
=======================================
The production is defined in the file "..._config.json".

Factory configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- "available": File will be read only if True
- "exit_if_end": Factory exits after execution only if True
- "run": Factory runs only if True

Configuration of single lines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- name": Name of the production line
- run": line runs only if True
- start_at": start position (start, storage or special machine)
- end_at": end position (END, storage or special machine)
- "with...": switch on/off different machines (nothing = off)
- color": color of the product



\
\

=======================================
How to change...
=======================================
All changes to the structure, sequence, etc. of the machines must be made exclusively in the :doc:`"...line" </rightline>` modules.


Sequence of machines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Change in :py:meth:`~rightline.RightLine.mainloop` in :doc:`"...line" </rightline>`.

Changing the positions of the robots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Change in the respective :py:meth:`run...() <rightline.RightLine.run_init>` function

Completely new machines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 - Create class as subclass of "machine
 - Create new function "run..." and integrate it into mainloop()

\
\

=======================================
Modules
=======================================


.. toctree::
   :maxdepth: 4
   :caption: Contents:

   setup
   leftline
   rightline
   mainline
   actuator
   sensor
   conveyor
   grip_robot
   index_line
   machine
   mp_station
   punch_mach
   robot_3d
   sort_line
   vac_robot
   warehouse
   exit_handler
   io_interface
   logger


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
