'''
Factory setup for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.15"

from time import sleep, time
from threading import Semaphore
from revpimodio2 import RevPiModIO

from lib.exit_handler import ExitHandler
from lib.io_interface import IOInterface
from lib.mqtt_handler import Configs, MqttHandler
from lib.logger import log
from lib.mainline import MainLine





class Setup():
    '''Setup for Factory.'''
    '''
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

        self.exit_handler = ExitHandler(self.revpi)
        # self.io_interface = IOInterface(input_file, output_file, states, self.factory_name, self.configs)
        self.mqtt_handler = MqttHandler(self.factory_name, self.states, self.configs)


    def run_factory(self):
        '''Starts the factory, adds and updates the lines.'''

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
                            self.lines[config["name"]] = self.line_class(self.revpi, config)
                            log.warning(f"Added new line: {config['name']}")
            
                self.__update_factory()
            except Exception as e:
                log.exception(e)
                self.exception = True

            # save Status of factory and every running machine
            # self.__save_status()
            
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
        self.mqtt_handler.disconnect()
        self.revpi.exit()


    def __update_factory(self):
        '''Updates the factory and starts every line.'''
        # check for error in lines
        line: MainLine
        for line in self.lines.values():
            # end the line
            if line.end_machine or line.config["run"] == False:
                log.critical(f"Stop: {line.name}")
                self.lines.pop(line.name)
                break

            if line.problem_in_machine:
                if self.configs.factory_commands.get("run") == False:
                    line.state = self.states.END
                else:
                    log.error(f"Problem in line {line.name}")
                    self.configs.factory_commands.update({"run", False})
            
            # handel exception in line
            if line.error_exception_in_machine:
                log.error(f"Error in line {line.name}")
                self.exit_handler.stop_factory()
                self.exception = True
                break
            
            # run an iteration if the line
            if line.running:
                line.update(self.configs.factory_commands.get("run"))
            # start the line
            elif line.config["run"] == True and (self.lines.get("Init") == None or self.lines.get("Init").running == False):
                log.critical(f"Start: {line.name}")
                line.switch_state(line.config["start_at"], False)
                line.running = True
                line.update(self.configs.factory_commands.get("run"))

        # stop factory if stop command was issued
        if self.configs.factory_commands.get("stop") == True:
            self.exit_handler.stop_factory()

        # end all lines if error occurred
        if self.exit_handler.was_called or self.exception:
            for line in self.lines.values():
                log.critical(f"Ending line: {line.name}")
                line.end_machine = True
            self.exception = True
            return


    def __save_status(self):
        '''Puts the states, factory status and line status into output.'''

        main_states = []
        factory_status = {}
        lines = {}
        
        # get the line states
        for state in self.states:
            main_states.append(state)

        # get factory status
        factory_status["running"] = self.io_interface.factory_run
        factory_status["exit_if_end"] = self.io_interface.factory_end
        
        # get the status dictionaries of all machines in all active lines
        line: MainLine
        for line in self.lines.values():
            if line.config["run"] == False:
                continue
            dictionary = {"self": line.status_dict}
            for machine in line.machines.values():
                dictionary[machine.name] = machine.get_status_dict()
            lines[line.name] = dictionary


        self.io_interface.update_output(main_states, factory_status, lines)
