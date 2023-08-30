'''This module handles json config read and write'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.08.30"

import json
from copy import deepcopy

from logger import log

class IOInterface():
    '''Handels json config read and program status update.
    
    update_configs_with_input(): Reads input file and appends the new configs to the configs list.
    __check_if_config_already_exists(): Returns True if the given config already exist.
    update_output(): Update program status.
    '''

    def __init__(self, input_file, output_file, states) -> None:
        '''Init IOInterface.
        
        :input_file: config json file where the mainloops are configured
        :output_file: json file where the states are logged
        :states: possible States of mainloop
        '''
        global log
        self.log = log.getChild(f"IO_Com")

        self.__input_file = input_file
        self.__output_file = output_file
        self.__states = states

        self.input_dict = {}
        self.__configs = []
        self.new_configs = []

        self.__output_dict = {}
        self.__update_num = 0


    # Methodes for input
    ###############################################################################################
    def update_configs_with_input(self):
        '''Reads input file and appends the new configs to the configs list.'''

        # check if file is available
        try:
            with open(self.__input_file, "r") as fp:
                json_dict: dict = json.load(fp)
        except json.JSONDecodeError:
            return
        if json_dict["available"] != True:
            return
        
        # get all the new configs
        new_configs = list(filter(lambda x: self.__check_if_config_already_exists(x) == False, json_dict["configs"]))

        # update the input dict
        if new_configs.__len__() > 0 or self.input_dict != json_dict:
            self.input_dict = deepcopy(json_dict)

        # inserts the correct states into the new configs
        for config in new_configs:
            for state in self.__states:
                if state.name == config["start_at"]:
                    config["start_at"] = state
                if state.name == config["end_at"]:
                    config["end_at"] = state
                if type(config["start_at"]) != str and type(config["end_at"]) != str:
                    break
            else:
                raise LookupError(f"Config {config['name']} could not be parsed for {state}")
        
        
        # add the new configs to the configs list 
        self.new_configs = new_configs   
        self.__configs.extend(new_configs)


    def __check_if_config_already_exists(self, config) -> bool:
        '''Returns True if the given config already exist.
        
        :config: the config dictionary to check
        '''
        for old_config in self.input_dict.get("configs", {}):
            if config == old_config:
                return True
        return False

    
    # Methodes for output
    ###############################################################################################
    
    def update_output(self, main_states: list, mainloops: dict):
        '''Update program status.

        :main_states: possible States of mainloop
        :mainloops: status data for all machines in all mainloops
        '''
        output_dict = {"update_num": self.__update_num}

        output_dict["states"] = []
        for state in main_states:
            state = f"{state.name:>14}, {state.value[1].name:<8}, {state.value[2]}"
            output_dict["states"].append(state)

        output_dict.update(mainloops)

        if output_dict == self.__output_dict:
            return

        self.__output_dict = output_dict
        
        try:
            # write to json file
            with open(self.__output_file, "w") as fp:
                json.dump(self.__output_dict, fp, indent=4)
        except Exception as e:
            self.log.exception(e)
        self.__update_num += 1

