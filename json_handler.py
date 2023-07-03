'''This module handles json config read and write'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.03"

import json

class JsonHandler():
    def read(self, json_file: str, states) -> "list[dict]":
        '''Reads json file and checks for errors.
        
        :json_file: path to file
        :states: possible States of mainloop
        -> list of dictionaries with config data
        '''
        with open(json_file, "r") as fp:
            configs = json.load(fp)["lines"]

        for config in configs:
            self.__check_variable(config, "name", str)
            self.__check_variable(config, "start_when", str)
            self.__check_variable(config, "start_at", str)
            self.__check_variable(config, "end_at", str)
            self.__check_variable(config, "with_oven", bool)
            self.__check_variable(config, "with_PM", bool)
            self.__check_variable(config, "with_WH", bool)
            self.__check_variable(config, "color", str)
            self.__check_variable(config, "running", bool)

            for state in states:
                if state.name == config["start_at"]:
                    config["start_at"] = state
                if state.name == config["end_at"]:
                    config["end_at"] = state
                if type(config["start_at"]) != str and type(config["end_at"]) != str:
                    break
            else:
                raise Exception(f"Config {config['name']}could not be parsed")
            
        return configs

    def __check_variable(self, config: dict, key: str, type):
        '''Check given key for existence and right type in config
        
        :config: config dictionary
        :key: key that should be checked
        :type: corresponding type
        '''
        try:
            variable = config[key]
        except KeyError:
            raise KeyError(f"Key \"{key}\" not found in config {config['name']}")
        if not isinstance(variable, type):
            raise TypeError(f"{variable} ist not type: {type} in config {config['name']}")