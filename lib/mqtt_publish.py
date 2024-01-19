'''Publish topics to mqtt broker
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.19"

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
        "name": "Line1", 
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
        "name": "Line2", 
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
        "name": "Line3", 
        "run": True,
        "start_at": "start",
        "end_at": "END",
        "with_PM": False,
        "with_WH": True,
        "color": "BLUE"
    },
    {
        "name": "Line4", 
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

        self.topic_start = f"MiniFactory/{factory_name}/Factory"

        self.client = mqtt.Client()

        self.client.connect(self.__BROKER_ADDR, self.__PORT)


        self.topic_line_config_set = f"{self.topic_start}/LineConfig/Set"
        self.topic_factory_config_set = f"{self.topic_start}/FactoryConfig/Set"
        self.topic_factory_command_set = f"{self.topic_start}/FactoryCommand/Set"
        self.topic_wh_content_set = f"{self.topic_start}/WHContent/Set"

        self.topic_line_config_get = f"{self.topic_start}/LineConfig/Get"
        self.topic_factory_config_get = f"{self.topic_start}/FactoryConfig/Get"
        self.topic_factory_command_get = f"{self.topic_start}/FactoryCommand/Get"
        self.topic_wh_content_get = f"{self.topic_start}/WHContent/Get"
        self.topic_machine_status_get = f"{self.topic_start}/MachineStatus/Get"
        self.topic_line_status_get = f"{self.topic_start}/LineStatus/Get"


    def publish_all(self):
        
        self.client.publish(self.topic_wh_content_set, json.dumps(wh_content))
        print(f"{self.topic_wh_content_set.removeprefix(f'{self.topic_start}/')}")

        # self.client.publish(self.topic_line_config_set, json.dumps({
        #     "name": "Test",
        #     "run": True,
        #     "start_at": "CB1",
        #     "end_at": "CB1"
        # }))
        # self.client.publish(self.topic_line_config_set, json.dumps({
        #     "name": "LineE4", 
        #     "run": True,
        #     "start_at": "CB1",
        #     "end_at": "CB3",
        #     "with_PM": True,
        #     "color": "WHITE"
        # }))


        # return

        # self.client.publish(self.topic_factory_command_set, json.dumps({"stop": True}))
        # print(f"{self.topic_factory_command_set.removeprefix(f'{self.topic_start}/')}")
        
        for config in line_configs:
            self.client.publish(self.topic_line_config_set, json.dumps(config))
            print(f"{self.topic_line_config_set.removeprefix(f'{self.topic_start}/')}")

        time.sleep(0.5)

        self.client.publish(self.topic_factory_command_set, json.dumps({"run": True}))
        print(f"{self.topic_factory_command_set.removeprefix(f'{self.topic_start}/')}")

        # self.client.publish(self.topic_line_config_get)
        # print(f"{self.topic_line_config_get.removeprefix(f'{self.topic_start}/')}")

        # self.client.publish(self.topic_line_status_get)
        # print(f"{self.topic_line_status_get.removeprefix(f'{self.topic_start}/')}")

        # time.sleep(1)
            
        # self.client.publish(self.topic_factory_command_set, json.dumps({"run": True}))
        # print(f"{self.topic_factory_command_set.removeprefix(f'{self.topic_start}/')}")

        # time.sleep(1)

        # self.client.publish(self.topic_line_config_get)
        # print(f"{self.topic_line_config_get.removeprefix(f'{self.topic_start}/')}")

        # self.client.publish(self.topic_line_status_get)
        # print(f"{self.topic_line_status_get.removeprefix(f'{self.topic_start}/')}")

        # time.sleep(1)


        self.client.publish(self.topic_factory_config_set, json.dumps({"exit_if_end": True}))
        print(f"{self.topic_factory_config_set.removeprefix(f'{self.topic_start}/')}")

        # time.sleep(3)

        # self.client.publish(self.topic_wh_content_get)
        # print(f"{self.topic_wh_content_get.removeprefix(f'{self.__topic_start}/')}")

        # # todo get working 
        # self.client.publish(self.topic_line_config_get)
        # print(f"{self.topic_line_config_get.removeprefix(f'{self.__topic_start}/')}")

        # self.client.publish(self.topic_factory_config_get)
        # print(f"{self.topic_factory_config_get.removeprefix(f'{self.__topic_start}/')}")

        print("End of publish all")

if __name__ == "__main__":
    mqtt_pub = MqttPublish(factory_name="Right")
    mqtt_pub.publish_all()
    print("end")