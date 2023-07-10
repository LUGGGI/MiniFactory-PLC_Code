'''Writes states as json'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.10"

import json

class StateLogger():
    update_num = 0

    def __init__(self, json_file: str) -> None:
        '''Initializes StateLogger.
        
        :json_file: path/file_name.json of file to which should be written
        '''
        self.json_file = json_file
    def update_file(self, states):
        '''Updates file with current states.

        :states: possible States of mainloop
        '''
        json_dict = {}
        try:
            # update update_nume
            json_dict["update_num"] = StateLogger.update_num
            StateLogger.update_num += 1
            states_list = []
            # get all states
            for state in states:
                states_list.append(f"{state.name:>14}, {state.value[1].name:<8}, {state.value[2]}")
            # update states
            json_dict["states"] = states_list
            
            # write to json file
            with open(self.json_file, "w") as fp:
                json.dump(json_dict, fp, indent=4)
        except:
            raise