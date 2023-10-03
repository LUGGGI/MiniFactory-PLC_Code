'''
Factory setup for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.09.15"

from time import sleep, time
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from io_interface import IOInterface
from logger import log
from mainline import MainLine


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
        exception (bool): True if exception in factory.
        loop_start_time (float): Current loop start time.
        last_config_update_time (float): Time of last config update.
        lines (dict): All Line objects currently active.
        exit_handler (ExitHandler): Object for Exit Handler.
        io_interface (IOInterface): Object for IO Interface.
    '''
    LOOP_TIME = 0.02 # in seconds
    
    def __init__(self, input_file, output_file, states, line_class):
        '''Init setup and setup of RevpiModIO.
        
        Args:
            input_file (str): Config json file path where the lines are configured.
            output_file (str): Json file path where the states are logged.
            states (State): All possible States of the line.
            line_class (Mainline): Class of the current line.
        '''
        # setup RevpiModIO
        try:
            self.revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            self.revpi = RevPiModIO(autorefresh=True, configrsc="../RevPi/RevPi82247.rsc", procimg="../RevPi/RevPi82247.img")
        
        self.revpi.mainloop(blocking=False)

        self.states = states
        self.line_class = line_class
        
        self.exception = False
        self.loop_start_time: float = 0
        self.last_config_update_time: float = 0

        self.lines: dict = {}

        self.exit_handler = ExitHandler(self.revpi)
        self.io_interface = IOInterface(input_file, output_file, states)


    def run_factory(self):
        '''Starts the factory, adds and updates the lines.'''

        while(True):
            self.loop_start_time = time()

            try:
                # update the config
                if time() > self.last_config_update_time + 1:
                    self.io_interface.update_configs_with_input()
                    self.last_config_update_time = time()

                    for config in self.io_interface.new_configs:
                        # add line if it doesn't exists
                        if self.lines.get(config["name"]) == None:
                            if config["run"] == False:
                                continue
                            self.lines[config["name"]] = self.line_class(self.revpi, config)
                            log.warning(f"Added new line: {config['name']}")
                        # update config in existing line
                        else:
                            self.lines[config["name"]].config = config
                            log.warning(f"Updated line: {config['name']}")
                    self.io_interface.new_configs.clear()
            
                self.__update_factory()
            except Exception as e:
                log.exception(e)
                self.exception = True

            # save Status of factory and every running machine
            self.__save_status()
            
            # exit the factory if error occurred or end has ben reached
            if self.exception:
                break
            if self.lines.__len__() <= 0 and self.io_interface.factory_end:
                break


            # wait the remaining runtime
            loop_run_time = time() - self.loop_start_time
            if loop_run_time < self.LOOP_TIME:
                sleep(self.LOOP_TIME - loop_run_time)
            else:
                log.debug(f"Long Loop run time: {(loop_run_time*1000).__round__()}ms")

        log.critical("End of program")
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
                if self.io_interface.factory_run == False:
                    line.state = self.states.END
                else:
                    log.error(f"Problem in line {line.name}")
                    self.io_interface.factory_run = False
            
            # handel exception in line
            if line.error_exception_in_machine:
                log.error(f"Error in line {line.name}")
                self.exit_handler.stop_factory()
                self.exception = True
                break
            
            # run an iteration if the line
            if line.running:
                line.update(self.io_interface.factory_run)
            # start the line
            elif line.config["run"] == True and (self.lines.get("Init") == None or self.lines.get("Init").running == False):
                log.critical(f"Start: {line.name}")
                line.switch_state(line.config["start_at"], False)
                line.running = True
                line.update(self.io_interface.factory_run)

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
