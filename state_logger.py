'''Writes states as json'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.12"

from time import sleep
import json
from logger import log

class StateLogger():
    __update_num = 0
    __json_file: str = None
    __json_dict: dict = None
    __update_available: bool = False
    __updating: bool = False

    def init(self, json_file: str, names_of_mainsloops: list) -> None:
        '''Initializes StateLogger.
        
        :json_file: path/file_name.json of file to which should be written
        :list_of_entries: name of every mainloop
        '''
        StateLogger.__json_file = json_file
        StateLogger.__json_dict = {"update_num": 0}
        StateLogger.__updating = False # is true while update to handle multithreading

        StateLogger.__json_dict.update({"states": []})
        for mainloop in names_of_mainsloops:
            StateLogger.__json_dict.update({mainloop: {}})
        self.update_main_states([])


    def update_main_states(self, states):
        '''Update main_states.

        :states: possible States of mainloop
        '''
        try:
            states_list = []
            # get all states
            for state in states:
                states_list.append(f"{state.name:>14}, {state.value[1].name:<8}, {state.value[2]}")
            # update states
            while (StateLogger.__updating):
                sleep(0.005)
            StateLogger.__updating = True
            
            StateLogger.__json_dict.update({"states": states_list})
        except Exception as error:
            log.exception(error)
        finally:
            StateLogger.__updating = False


    def update_machine(self, mainloop_name: str, machine_name: str, machine_status):
        '''Update machine state.

        :mainloop_name: name of current mainloop
        :machine_name: name of machine
        :machine_status: list of status variables of machine
        '''
        try:
            if machine_name.find("_") != -1:
                return
            # update states
            while (StateLogger.__updating):
                sleep(0.005)
            StateLogger.__updating = True
            
            
            if StateLogger.__json_dict[mainloop_name].get(machine_name) != machine_status:
                StateLogger.__json_dict[mainloop_name].update({machine_name: machine_status})
                StateLogger.__update_available = True
            
        except Exception as error:
            log.exception(error)
        finally:
            StateLogger.__updating = False
            


    def update_file(self):
        '''Wirte json dictionary to file'''
        if StateLogger.__update_available == False:
            return
        StateLogger.__update_available = False
        try:
            while (StateLogger.__updating):
                sleep(0.005)
            StateLogger.__updating = True
            # update update_num
            StateLogger.__update_num += 1
            StateLogger.__json_dict["update_num"] = StateLogger.__update_num

            # write to json file
            with open(StateLogger.__json_file, "w") as fp:
                json.dump(StateLogger.__json_dict, fp, indent=4)

        except Exception as error:
            log.exception(error)
        finally:
            StateLogger.__updating = False