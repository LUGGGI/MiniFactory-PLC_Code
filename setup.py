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
from logger import log
from state_logger import StateLogger
from mainloop import MainLoop

class Setup():
    '''Setup Mainloop'''
    LOOP_TIME = 0.02 # in seconds
    
    def __init__(self) -> None:
        '''Init setup and setup RevpiModIO'''
        # setup RevpiModIO
        try:
            self.revpi = RevPiModIO(autorefresh=True)
        except:
            # load simulation if not connected to factory
            self.revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/Code/RevPi/RevPi82247.img")
        
        self.revpi.mainloop(blocking=False)
        self.exit_handler = ExitHandler(self.revpi)
        
        self.stage = None
        self.main_loops: "list[MainLoop]" = []
        self.state_logger = StateLogger()


    def run_factory(self):
        '''Runs the factory and starts every mainloop.'''

        # init state_logger
        names_of_mainsloops = []
        for main_loop in self.main_loops:
            names_of_mainsloops.append(main_loop.name)
        self.state_logger.init("states.json", names_of_mainsloops)

        loop_start_time: float = 0
        exception = False
        while(self.main_loops.__len__() > 0 and not exception):
            loop_start_time = time()
            # check for error in mainloops
            for main_loop in self.main_loops:
                # run an iteration if the mainloop
                if main_loop.running:
                    main_loop.update()
                # start the mainloop
                elif main_loop.config["start_when"] == self.stage or main_loop.config["start_when"] == "now":
                    log.critical(f"Start: {main_loop.name}")
                    main_loop.switch_state(main_loop.config["start_at"], False)
                    main_loop.running = True
                
                # end the mainloop
                if main_loop.end_machine:
                    self.stage = main_loop.name
                    log.critical(f"Stop: {main_loop.name}")
                    self.main_loops.remove(main_loop)
                    break
                
                # handel exception in mainloop
                if main_loop.error_exception_in_machine:
                    log.error(f"Error in mainloop {main_loop.name}")
                    self.exit_handler.stop_factory()
                    exception = True
                    break

            # end all mainloops if error occurred
            if self.exit_handler.was_called or exception:
                for main_loop in self.main_loops:
                    log.critical(f"Ending mainloop: {main_loop.name}")
                    main_loop.end_machine = True
                return
            
            
            self.state_logger.update_file()
            loop_run_time = time() - loop_start_time
            log.debug(f"Loop run time: {loop_run_time}")
            sleep(self.LOOP_TIME - loop_run_time if loop_run_time < self.LOOP_TIME else 0)
