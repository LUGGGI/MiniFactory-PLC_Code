'''Handels Communication with mqtt broker.

Topics: MiniFactory/Right/Factory/LineConfig
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.12.06"

import json
import paho.mqtt.client as mqtt

try:
    from lib.logger import log
except ModuleNotFoundError:
    from logger import log

class MqttInterface():
    '''Handels Communication with mqtt broker.'''

    __BROKER_ADDR = "192.168.0.59"
    __PORT = 1883
    __TOPIC_LINE_CONFIG = "LineConfig"
    __TOPIC_FACTORY_CONFIG = "FactoryConfig"
    __TOPIC_FACTORY_COMMAND = "FactoryCommand"
    __TOPIC_UPDATE_WH = "UpdateWH"

    def __init__(self, factory_name) -> None:
        '''Init MqttInterface.
        
        Args:
            factory_name (str): Name of the factory (for example Right)
        '''

        # self.__BROKER_ADDR = "test.mosquitto.org"

        global log
        self.log = log.getChild(f"Mqtt")

        self.topic_start = f"MiniFactory/{factory_name}/Factory"



        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect

        self.client.message_callback_add(f"{self.topic_start}/{self.__TOPIC_LINE_CONFIG}", self.on_message_line_config)
        self.client.message_callback_add(f"{self.topic_start}/{self.__TOPIC_FACTORY_CONFIG}", self.on_message_factory_config)
        self.client.message_callback_add(f"{self.topic_start}/{self.__TOPIC_FACTORY_COMMAND}", self.on_message_factory_command)
        self.client.on_message = self.on_message_fallback

        self.client.on_disconnect = self.on_disconnect

        self.client.connect(self.__BROKER_ADDR, self.__PORT)

        self.client.loop_start()


    def on_connect(self, client: mqtt.Client, _userdata, _flags, rc):
        '''Connection callback.
        
        Args:
            client(mqtt.Client): connection client.
        '''
        log.warning(f"Connected to MQTT-Broker. Result code: {rc}")

        client.subscribe("Debug")
        client.subscribe("Status")
        client.subscribe(f"{self.topic_start}/{self.__TOPIC_LINE_CONFIG}")
        client.subscribe(f"{self.topic_start}/{self.__TOPIC_FACTORY_CONFIG}")
        client.subscribe(f"{self.topic_start}/{self.__TOPIC_FACTORY_COMMAND}")


    def on_message_line_config(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the LineConfig topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        print(f"LineConfig: {json.loads(msg.payload)}")


    def on_message_factory_config(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the FactoryConfig topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        print(f"FactoryConfig: {json.loads(msg.payload)}")


    def on_message_factory_command(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the FactoryCommand topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        print(f"FactoryCommand: {json.loads(msg.payload)}")


    def on_message_fallback(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new message that couldn't be filtered in other callbacks.'''

        log.warning(f"Message received for topic {msg.topic}: {msg.payload}")


    def on_disconnect(self, client, userdata, rc):
        '''Disconnection callback.'''
        log.warning("Connection to MQTT-Broker disconnected")



if __name__ == "__main__":
    MqttInterface(factory_name="Right")
    input("Press Enter to end")