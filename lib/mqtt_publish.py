'''Publish topics to mqtt broker
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.12.18"

import json
import paho.mqtt.client as mqtt
import time


read = True

line_configs = [
    {
        "name": "Init", 
        "run": True,
        "start_at": "INIT",
        "end_at": "END"
    },
    {
        "name": "Main1", 
        "run": True,
        "start_at": "start",
        "end_at": "END",
        "with_oven": True,
        "with_saw": True,
        "with_PM": False,
        "with_WH": False,
        "color": "WHITE"
    },
    {
        "name": "Main2", 
        "run": True,
        "start_at": "start",
        "end_at": "storage",
        "with_oven": False,
        "with_saw": True,
        "with_PM": True,
        "with_WH": True,
        "color": "RED"
    },
    {
        "name": "Main3", 
        "run": True,
        "start_at": "start",
        "end_at": "END",
        "with_PM": False,
        "with_WH": True,
        "color": "BLUE"
    },
    {
        "name": "Main4", 
        "run": True,
        "start_at": "storage",
        "end_at": "END",
        "color": "RED"
    }
]

factory_config = {
    "exit_if_end": True
}

factory_command = {
    "run": True,
    "stop": False
}

wh_content = [
        [
            "Carrier",
            "Carrier",
            "Carrier"
        ],
        [
            "WHITE",
            "RED",
            "BLUE"
        ],
        [
            "Carrier",
            "Carrier",
            "Carrier"
        ]
    ]

class MqttPublish():
    '''Handels Publishing to mqtt broker.
    '''

    __BROKER_ADDR = "192.168.0.59"
    __PORT = 1883

    def __init__(self, factory_name: str) -> None:
        '''Init MqttInterface.
        
        Args:
            factory_name (str): Name of the factory (for example Right).
            states (State): Possible States of line.
        '''

        self.__BROKER_ADDR = "test.mosquitto.org"

        self.__topic_start = f"MiniFactory/{factory_name}/Factory"

        self.__client = mqtt.Client()

        self.__client.connect(self.__BROKER_ADDR, self.__PORT)


        self.topic_line_config_set = f"{self.__topic_start}/LineConfig/Set"
        self.topic_factory_config_set = f"{self.__topic_start}/FactoryConfig/Set"
        self.topic_factory_command_set = f"{self.__topic_start}/FactoryCommand/Set"
        self.topic_wh_content_set = f"{self.__topic_start}/WHContent/Set"

        self.topic_wh_content_get = f"{self.__topic_start}/WHContent/Get"
        self.topic_line_config_get = f"{self.__topic_start}/LineConfig/Get"

        self.publish_all()


    def publish_all(self):
        if read == False:
            print("Read is set to False")
            return
        
        self.__client.publish(self.topic_wh_content_set, json.dumps(wh_content))
        print(f"{self.topic_wh_content_set.removeprefix(f"{self.__topic_start}/")}")

        for config in line_configs:
            self.__client.publish(self.topic_line_config_set, json.dumps(config))
            print(f"{self.topic_line_config_set.removeprefix(f"{self.__topic_start}/")}")

        # self.__client.publish(self.topic_factory_command_set, json.dumps(factory_command))
        # print(f"{self.topic_factory_command_set.removeprefix(f"{self.__topic_start}/")}")

        # self.__client.publish(self.topic_factory_config_set, json.dumps(factory_config))
        # print(f"{self.topic_factory_config_set.removeprefix(f"{self.__topic_start}/")}")


        time.sleep(1)

        self.__client.publish(self.topic_wh_content_get)
        print(f"{self.topic_wh_content_get.removeprefix(f"{self.__topic_start}/")}")

        self.__client.publish(self.topic_line_config_get)
        print(f"{self.topic_line_config_get.removeprefix(f"{self.__topic_start}/")}")

        print("End of publish all")

if __name__ == "__main__":
    MqttPublish(factory_name="Right")