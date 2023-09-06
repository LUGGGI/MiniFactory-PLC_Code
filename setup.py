'''
Main Loop config for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.08.30"

from time import sleep, time
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from io_interface import IOInterface
from logger import log
from mainloop import MainLoop


class Setup():
    '''Setup Mainloop.
    
    update_factory(): Updates the factory and starts every mainloop.
    save_status(): Gets the mainloop states and the status dictionaries of all machines in all active mainloops. Puts them into output.
    '''
    LOOP_TIME = 0.02 # in seconds
    
    def __init__(self, input_file, output_file, states, mainloop_class) -> None:
        '''Init setup and setup RevpiModIO
        
        :input_file: config json file where the mainloops are configured
        :output_file: json file where the states are logged
        :states: possible States of mainloop
        '''
        # setup RevpiModIO
        try:
            self.revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            self.revpi = RevPiModIO(autorefresh=True, configrsc="../RevPi/RevPi82247.rsc", procimg="../RevPi/RevPi82247.img")
        
        self.revpi.mainloop(blocking=False)

        self.states = states
        self.mainloop_class = mainloop_class
        
        self.stage = None
        self.exception = False
        self.loop_start_time: float = 0
        self.last_config_update_time: float = 0

        self.mainloops: dict = {}

        self.exit_handler = ExitHandler(self.revpi)
        self.io_interface = IOInterface(input_file, output_file, states)


    def run_factory(self):
        '''Starts the factory, adds and updates the mainloops'''
        self.io_interface.update_configs_with_input()

        while(True):
            self.loop_start_time = time()

            for config in self.io_interface.new_configs:
                # add mainloop if it doesn't exists
                if self.mainloops.get(config["name"]) == None:
                    if config["run"] == False:
                        continue
                    self.mainloops[config["name"]] = self.mainloop_class(self.revpi, config)
                    log.warning(f"Added new Mainloop: {config['name']}")
                # update config in existing mainloop
                else:
                    self.mainloops[config["name"]].config = config
                    log.warning(f"Updated Mainloop: {config['name']}")
            self.io_interface.new_configs.clear()

            try:
                self.__update_factory()
            except Exception as e:
                log.exception(e)
                self.exception = True

            # save Status of factory and every running machine
            self.__save_status()
            
            # exit the factory if error occurred or end has ben reached
            if self.exception:
                break
            if self.mainloops.__len__() <= 0 and self.io_interface.input_dict["exit_if_end"]:
                break
            
            
            # update the config
            if time() > self.last_config_update_time + 5:
                self.io_interface.update_configs_with_input()
                self.last_config_update_time = time()

            # wait the remaining runtime
            loop_run_time = time() - self.loop_start_time
            if loop_run_time < self.LOOP_TIME:
                sleep(self.LOOP_TIME - loop_run_time)
            else:
                log.debug(f"Long Loop run time: {(loop_run_time*1000).__round__()}ms")

        log.critical("End of program")
        self.revpi.exit()


    def __update_factory(self):
        '''Updates the factory and starts every mainloop.'''
        # check for error in mainloops
        mainloop: MainLoop
        for mainloop in self.mainloops.values():
            # run an iteration if the mainloop
            if mainloop.running:
                mainloop.update(self.io_interface.input_dict["run"])
            # start the mainloop
            elif mainloop.config["run"] == True and (self.mainloops.get("Init") == None or self.mainloops.get("Init").running == False):
                log.critical(f"Start: {mainloop.name}")
                mainloop.switch_state(mainloop.config["start_at"], False)
                mainloop.running = True
                mainloop.update(self.io_interface.input_dict["run"])
            
            # end the mainloop
            if mainloop.end_machine or mainloop.config["run"] == False:
                self.stage = mainloop.name
                log.critical(f"Stop: {mainloop.name}")
                self.mainloops.pop(mainloop.name)
                break
            
            # handel exception in mainloop
            if mainloop.error_exception_in_machine:
                log.error(f"Error in mainloop {mainloop.name}")
                self.exit_handler.stop_factory()
                self.exception = True
                break

            # end all mainloops if error occurred
            if self.exit_handler.was_called or self.exception:
                for mainloop in self.mainloops:
                    log.critical(f"Ending mainloop: {mainloop.name}")
                    mainloop.end_machine = True
                    self.exception = True
                return


    def __save_status(self):
        '''Gets the mainloop states and the status dictionaries of all machines in all active mainloops. Puts them into output.'''

        main_states = []
        mainloops = {}
        
        # get the mainloop states
        for state in self.states:
            main_states.append(state)
        
        # get the status dictionaries of all machines in all active mainloops
        mainloop: MainLoop
        for mainloop in self.mainloops.values():
            if mainloop.config["run"] == False:
                continue
            dictionary = {"self": mainloop.status_dict}
            for machine in mainloop.machines.values():
                dictionary[machine.name] = machine.get_status_dict()
            mainloops[mainloop.name] = dictionary


        self.io_interface.update_output(main_states, mainloops)
