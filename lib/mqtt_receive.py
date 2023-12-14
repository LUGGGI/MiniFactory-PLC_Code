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


class MqttReceive():
    '''Handels Receiving with mqtt broker.
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
        self.__client.on_connect = self.__on_connect

        self.__client.on_message = self.__on_message_fallback

        self.__client.on_disconnect = self.__on_disconnect

        self.__client.connect(self.__BROKER_ADDR, self.__PORT)

        self.__client.loop_forever()


    def disconnect(self):
        '''Disconnect from MQTT broker.'''
        self.__client.disconnect()


    def __on_connect(self, client: mqtt.Client, _userdata, _flags, rc):
        '''Connection callback.
        
        Args:
            client(mqtt.Client): connection client.
        '''
        print(f"Connected to MQTT-Broker. Result code: {rc}")

        client.subscribe("Debug")
        client.subscribe("Status")
        client.subscribe(f"{self.__topic_start}/#")
        # client.subscribe(f"{self.__topic_start}/WHContent")
        # client.subscribe(f"{self.__topic_start}/WHContent/Get")
        # client.subscribe(f"{self.__topic_start}/WHContent/Data")

    def __on_message_fallback(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new message that couldn't be filtered in other callbacks.'''
        try:
            decoded_msg = json.loads(msg.payload)
        except Exception:
            decoded_msg = msg.payload
        print(f"Message received for topic {msg.topic}: \n\t{decoded_msg}")


    def __on_disconnect(self, client, userdata, rc):
        '''Disconnection callback.'''
        print("Connection to MQTT-Broker disconnected")    


if __name__ == "__main__":
    MqttReceive(factory_name="Right")