'''
Main Loop config for MiniFactory project
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.24"

from time import sleep, time
from revpimodio2 import RevPiModIO

from exit_handler import ExitHandler
from io_interface import IOInterface
from logger import log
from mainloop import MainLoop


class Setup():
    '''Setup Mainloop'''
    LOOP_TIME = 0.02 # in seconds
    
    def __init__(self, input_file, output_file, states) -> None:
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
            self.revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.img")
        
        self.revpi.mainloop(blocking=False)

        self.states = states
        
        self.stage = None
        self.exception = False
        self.loop_start_time: float = 0
        self.last_config_update_time: float = 0

        self.mainloops: dict = {}

        self.exit_handler = ExitHandler(self.revpi)
        self.io_interface = IOInterface(input_file, output_file, states)


    def update_factory(self):
        '''Updates the factory and starts every mainloop.'''

        # check for error in mainloops
        mainloop: MainLoop
        for mainloop in self.mainloops.values():
            # run an iteration if the mainloop
            if mainloop.running:
                mainloop.update()
            # start the mainloop
            elif mainloop.config["start"] == True:
                log.critical(f"Start: {mainloop.name}")
                mainloop.switch_state(mainloop.config["start_at"], False)
                mainloop.running = True
            
            # end the mainloop
            if mainloop.end_machine:
                self.stage = mainloop.name
                log.critical(f"Stop: {mainloop.name}")
                self.mainloops.remove(mainloop)
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
            
            
        self.save_status()

        if time() > self.last_config_update_time + 5:
            self.io_interface.update_configs_with_input()
            self.last_config_update_time = time()

        loop_run_time = time() - self.loop_start_time
        log.debug(f"Loop run time: {loop_run_time}")
        sleep(self.LOOP_TIME - loop_run_time if loop_run_time < self.LOOP_TIME else 0)


    def save_status(self):
        '''Gets the mainloop states and the status dictionaries of all machines in all active mainloops. Puts them into output'''

        main_states = []
        mainloops = {}
        
        # get the mainloop states
        for state in self.states:
            main_states.append(state)
        
        # get the status dictionaries of all machines in all active mainloops
        mainloop: MainLoop
        for mainloop in self.mainloops.values():
            if mainloop.config["start"] == False:
                continue
            dictionary = {"self": mainloop.status_dict}
            for machine in mainloop.machines.values():
                dictionary[machine.name] = machine.get_status_dict()
            mainloops[mainloop.name] = dictionary


        self.io_interface.update_output(main_states, mainloops)