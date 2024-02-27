'''
Factory setup for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.19"

from time import sleep, time
from revpimodio2 import RevPiModIO

from lib.exit_handler import ExitHandler
from lib.mqtt_handler import Configs, Status, MqttHandler
from lib.logger import log
from lib.machine import MainState
from lib.mainline import MainLine


class Setup():
    '''Setup for Factory.

    Methodes:
        run_factory(): Starts the factory, adds and updates the lines.
        __update_factory(): Updates the factory and starts every line.
        __save_status(): Puts the states, factory status and line status into output.
    Attributes:
        LOOP_TIME (int): How often a new iteration is started (in seconds).
        revpi (RevPiModIO): RevPiModIO Object to control the motors and sensors.
        states (State): All possible States of the line.
        line_class (Mainline): Class of the current line.
        factory_name (str): Name of the factory (for example Right).
        exception (bool): True if exception in factory.
        loop_start_time (float): Current loop start time.
        last_config_update_time (float): Time of last config update.
        lines (dict): All Line objects currently active.
        exit_handler (ExitHandler): Object for Exit Handler.
        io_interface (IOInterface): Object for IO Interface.
    '''
    LOOP_TIME = 0.02 # in seconds
    
    def __init__(self, states, line_class: MainLine, factory_name: str):
        '''Init setup and setup of RevpiModIO.
        
        Args:
            states (State): All possible States of the line.
            line_class (Mainline): Class of the current line.
            factory_name (str): Name of the factory (for example Right).
        '''
        log.critical(f"Initializing {factory_name}-Factory")
        # setup RevpiModIO
        try:
            self.revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            self.revpi = RevPiModIO(autorefresh=True, configrsc="../RevPi/right.rsc", procimg="../RevPi/right.img")
        
        self.revpi.mainloop(blocking=False)

        self.states = states
        self.line_class = line_class
        self.factory_name = factory_name
        
        self.exception = False
        self.loop_start_time: float = 0
        self.last_config_update_time: float = 0
        self.last_led_update_time: float = 0
        self.status_led = 0
        self.status_led_blink = True

        self.lines: dict = {}
        self.configs = Configs()
        self.status = Status()

        self.exit_handler = ExitHandler(self.revpi)
        self.mqtt_handler = MqttHandler(self.factory_name, self.configs, self.status)


    def run_factory(self):
        '''Starts the factory, adds and updates the lines.'''
        
        self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, "Program started")
        self.set_status_led(factory_led="green")
        # send all the machineStatus-Data
        for state in self.states:
            state_data = {state.name: [state.value[1].name, state.value[2]]}
            self.status.machine_status.update(state_data)
        self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_MACHINE_STATUS)

        while(True):
            self.loop_start_time = time()

            try:
                # update the config
                if time() > self.last_config_update_time + 1:
                    self.last_config_update_time = time()

                    config: dict
                    for config in self.configs.line_configs.values():
                        # add line if it doesn't exists
                        if config.pop("new", False) == True:
                            self.lines[config["name"]] = self.line_class(self.revpi, self.convert_to_states(config))
                            log.warning(f"Added new line: {config['name']}")
                            self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, f"New line added: {config}")
            
                self.__update_factory()
                # save Status of factory, lines and every running machine
                self.__save_status()

                self.set_status_led()
            except Exception as error:
                self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, {"ERROR": self.convert_exception_to_str(error)})
                log.exception(f"ERROR: {error}")
                self.exception = True

            
            # exit the factory if error occurred or end has ben reached
            if self.exception:
                break
            if self.lines.__len__() <= 0 and self.configs.factory_config.get("exit_if_end"):
                break


            # wait the remaining runtime
            loop_run_time = time() - self.loop_start_time
            if loop_run_time < self.LOOP_TIME:
                sleep(self.LOOP_TIME - loop_run_time)
            else:
                log.debug(f"Long Loop run time: {(loop_run_time*1000).__round__()}ms")

        if self.exception:
            self.set_status_led(factory_led="red")
        else:
            self.set_status_led(factory_led="off")
        log.critical("End of program")
        self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, "Program stopped")
        self.mqtt_handler.disconnect()
        self.revpi.exit()


    def __update_factory(self):
        '''Updates the factory and starts every line.'''
        # check for error in lines
        line: MainLine
        for line in self.lines.values():
            # update the line config with new data from mqtt_handler
            if self.configs.line_configs.get(line.name).pop("changed", False):
                line.config = self.convert_to_states(self.configs.line_configs.get(line.name))
                log.warning(f"Changed line: {line.name}")
                self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, f"Changed line: {line.name}")
            # end the line
            if line.end_line:
                if line.config["run"] == True:
                    log.critical(f"Stop: {line.name}")
                    self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, f"Stopped line: {line.name}")
                    line.config["run"] = False
                    self.configs.line_configs[line.name]["run"] = False
                # remove line only when restarting
                if self.configs.factory_commands["run"] == True:
                    self.lines.pop(line.name)
                    self.configs.line_configs.pop(line.name)
                    self.status.line_status.pop(line.name)
                    if self.lines.__len__() == 0:
                        self.set_status_led(line_led="off")
                    break
            # handle problems in the line
            if line.state == MainState.PROBLEM:
                if self.configs.factory_commands["run"] == True:
                    log.error(f"Problem in line {line.name}: {line.exception_msg}")
                    self.configs.factory_commands.update({"run": False})
                    self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_COMMANDS, {"run": False})
                    self.set_status_led(line_led="red")
            
            # handel exception in the line
            if line.state == MainState.ERROR:
                self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, {"ERROR": f"Error in line {line.name}: {self.convert_exception_to_str(line.exception_msg)}"})
                self.set_status_led(line_led="red")
                log.error(f"Error in line {line.name}: {line.exception_msg}")
                self.__save_status()
                self.exception = True
                break
            
            # run an iteration if the line
            if line.running:
                line.update(self.configs.factory_commands.get("run"))
                
            # start the line
            elif line.config["run"] == True and (self.lines.get("Init") == None or self.lines.get("Init").running == False) and self.configs.factory_commands.get("run"):
                log.critical(f"Start: {line.name}")
                line.switch_state(line.config["start_at"], False)
                line.running = True
                self.set_status_led(line_led="green")

        # end all lines if error occurred or if stop command was issued
        if self.exit_handler.was_called or self.exception or self.configs.factory_commands.get("stop"):
            self.configs.factory_commands.update({"stop": True})
            self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_COMMANDS, {"stop": True})

            for line in self.lines.values():
                log.critical(f"Ending line: {line.name}")
                line.end_line = True

            if not self.exit_handler.was_called:
                self.exit_handler.stop_factory()

            self.exception = True
            return


    def __save_status(self):
        '''Saves the machines status, factory status and line status.'''
        
        # get the machine states
        for state in self.states:
            state_data = {state.name: [state.value[1].name, state.value[2]]}
            old_state_data = self.status.machine_status.get(state.name)
            if old_state_data != state_data[state.name]:
                # if state changed update status and send the state_data
                self.status.machine_status.update(state_data)
                # if state_data[state.name][0] == "BLOCKED" or (old_state_data[0] == "BLOCKED" and state_data[state.name][0] == "FREE"):
                #     # skip sending if state just was set to block
                #     continue
                self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_MACHINE_STATUS, state_data)
                self.status.status_update_num += 1
        
        # get the status of all lines
        line: MainLine
        for line in self.lines.values():
            if line.config["run"] == False:
                continue
            line_status = {"self": {
                "state": line.state.name if line.state else None, 
                "product_at": line.product_at
                }}
            if line.waiting_for_state:
                line_status.update({"waiting_for": line.waiting_for_state.name})
            
            for machine in line.machines.values():
                line_status.update({machine.name: {"status": machine.state.name if machine.state else None}})
                if machine.state == MainState.WARNING:
                    line_status[machine.name].update({"WARNING": self.convert_exception_to_str(machine.exception_msg)})
                if machine.state == MainState.PROBLEM:
                    line_status[machine.name].update({"PROBLEM": self.convert_exception_to_str(machine.exception_msg)})
                if machine.state == MainState.ERROR:
                    line_status[machine.name].update({"ERROR": self.convert_exception_to_str(machine.exception_msg)})

            if line_status != self.status.line_status.get(line.name):
                self.status.line_status.update({line.name: line_status})
                self.status.status_update_num += 1
                self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_LINE_STATUS, {line.name: line_status})


    def convert_to_states(self, config_dict: dict) -> dict:
        '''Converts all the state names to actual states'''
        config = config_dict.copy()
        if config.get("start_at", "start").lower() == "start":
                config["start_at"] = "GR1"
        elif config["start_at"].lower() == "storage":
            config["start_at"] = "WH_RETRIEVE"
        if config.get("end_at", "storage").lower() == "storage":
            config["end_at"] = "WH_STORE"
        for state in self.states:
            if state.name == config["start_at"]:
                config["start_at"] = state
            if state.name == config["end_at"]:
                config["end_at"] = state
            if type(config["start_at"]) != str and type(config["end_at"]) != str:
                break
        else:
            if config["start_at"] == "INIT":
                config["start_at"] = MainState.INIT
            if config["end_at"] == "END":
                config["end_at"] = MainState.END
            else:
                raise LookupError(f"Config {config['name']} could not be parsed.")
        
        return config


    def convert_exception_to_str(self, exception: Exception) -> str:
        '''Converts an exception into a formatted string.
        
        Args:
            exception(Exception): exception to be converted.
        '''
        return f"{type(exception).__name__}: {exception}"


    def set_status_led(self, factory_led: str=None, line_led: str=None):
        '''Sets the status LEDs according to the status of the factory.

        Args:
            a1(str): Factory status, color of a1 led (red, green, off).
            a2(str): Line status, color of a1 led (red, green, off).
        
        A1:
            Green blinking: Factory running
            Red blinking: Problem with factory
            static/ off: Factory stopped
        A2:
            Green blinking: A line is running
            Red blinking: Problem in a line
            static/ off: Line stopped
        '''

        if factory_led == "green":
            self.status_led = self.status_led & int("1100", 2)
            self.status_led = self.status_led | int("0001", 2)
        if factory_led == "red":
            self.status_led = self.status_led & int("1100", 2)
            self.status_led = self.status_led | int("0010", 2)
        if factory_led == "off":
            self.status_led = self.status_led & int("1100", 2)
        
        if line_led == "green":
            self.status_led = self.status_led & int("0011", 2)
            self.status_led = self.status_led | int("0100", 2)
        if line_led == "red":
            self.status_led = self.status_led & int("0011", 2)
            self.status_led = self.status_led | int("1000", 2)
        if line_led == "off":
            self.status_led = self.status_led & int("0011", 2)

        if time() > self.last_led_update_time + 1 or factory_led or line_led:
            if self.status_led_blink == False or factory_led or line_led:
                self.status_led_blink = True
                self.revpi.io.RevPiLED.value = self.status_led
            else:
                self.status_led_blink = False
                self.revpi.io.RevPiLED.value = 0

            self.last_led_update_time = time()