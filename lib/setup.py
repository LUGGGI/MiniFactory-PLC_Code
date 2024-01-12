'''
Factory setup for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.12"

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
    
    def __init__(self, input_file: str, output_file: str, states, line_class: MainLine, factory_name: str):
        '''Init setup and setup of RevpiModIO.
        
        Args:
            input_file (str): Config json file path where the lines are configured.
            output_file (str): Json file path where the states are logged.
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

        self.lines: dict = {}
        self.configs = Configs()
        self.status = Status()

        self.exit_handler = ExitHandler(self.revpi)
        self.mqtt_handler = MqttHandler(self.factory_name, self.configs, self.status)


    def run_factory(self):
        '''Starts the factory, adds and updates the lines.'''
        
        self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_STATUS, "Program started")
        # send all the machineStatus-Data
        for state in self.states:
            state_data = {state.name: [state.value[1].name, state.value[2]]}
            self.status.machines_status.update(state_data)
        self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_MACHINES_STATUS)

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
            
                self.__update_factory()
            except Exception as e:
                log.exception(e)
                self.exception = True

            # save Status of factory, lines and every running machine
            self.__save_status()
            
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
            # end the line
            if line.end_line:
                log.critical(f"Stop: {line.name}")
                self.lines.pop(line.name)
                self.configs.line_configs.pop(line.name)
                break
            # handle problems in the line
            if line.state == MainState.PROBLEM:
                if self.configs.factory_commands["run"] == True:
                    log.error(f"Problem in line {line.name}: {line.exception_msg}")
                    self.configs.factory_commands.update({"run": False})
                    self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_FACTORY_COMMANDS, {"run": False})
            
            # handel exception in the line
            if line.state == MainState.ERROR:
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
            if self.status.machines_status.get(state.name) != state_data[state.name]:
                # if state changed update status and send the state_data
                self.status.machines_status.update(state_data)
                self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_MACHINES_STATUS, state_data)
                self.status.status_update_num += 1
        
        # get the status of all lines and its machines
        changed = False
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
                if machine.state == MainState.PROBLEM:
                    line_status[machine.name].update({"PROBLEM": self.convert_exception_to_str(machine.exception_msg)})
                if machine.state == MainState.ERROR:
                    line_status[machine.name].update({"ERROR": self.convert_exception_to_str(machine.exception_msg)})

            if line_status != self.status.line_status.get(line.name):
                self.status.line_status.update({line.name: line_status})
                changed = True
        if changed:
            self.status.status_update_num += 1
            self.mqtt_handler.send_data(self.mqtt_handler.TOPIC_LINE_STATUS)


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
            if config["end_at"] == "END":
                config["end_at"] == MainState.END
            else:
                raise LookupError(f"Config {config['name']} could not be parsed.")
        
        return config


    def convert_exception_to_str(self, exception: Exception) -> str:
        '''Converts an exception into a formatted string.
        
        Args:
            exception(Exception): exception to be converted.
        '''
        return f"{type(exception).__name__}: {exception}"