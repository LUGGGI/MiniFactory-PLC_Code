'''Handels Communication with mqtt broker.
'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2024.01.12"

import json
import paho.mqtt.client as mqtt

try:
    from lib.logger import log
except ModuleNotFoundError:
    from logger import log

class Configs():
    '''Holds config and commands for factory and production lines.'''

    line_configs: "dict[str, dict]" = {}
    factory_config = {
        "exit_if_end": False
    }
    factory_commands = {
        "run": False,
        "stop": False
    }

class Status():
    '''Holds the current status of the different factory parts.'''

    status_update_num = 0
    machine_status = {}
    line_status = {}


class MqttHandler():
    '''Handels Communication with mqtt broker.
    
    Attributes:
        configs (Configs): Object where all config data can be saved.
    '''

    __BROKER_ADDR = "192.168.0.59"
    __PORT = 1883

    TOPIC_LINE_CONFIG = "LineConfig"
    TOPIC_FACTORY_CONFIG = "FactoryConfig"
    TOPIC_FACTORY_COMMANDS = "FactoryCommand"

    TOPIC_WH_CONTENT = "WHContent"
    TOPIC_MACHINE_STATUS = "MachineStatus"
    TOPIC_FACTORY_STATUS = "FactoryStatus"
    TOPIC_LINE_STATUS = "LineStatus"
    
    

    def __init__(self, factory_name: str, configs: Configs, status: Status) -> None:
        '''Init MqttInterface.
        
        Args:
            factory_name (str): Name of the factory (for example Right).
            configs (Configs): Object where all config data can be saved.
            status (Status): Holds the current status of the different factory parts.
        '''

        self.__BROKER_ADDR = "test.mosquitto.org"

        global log
        self.log = log.getChild(f"Mqtt")

        self.__topic_start = f"MiniFactory/{factory_name}/Factory"
        self.__wh_content_file = f"{factory_name.lower()}_wh_content.json"
        self.__configs = configs
        self.__status = status

        self.__topics = {
            self.TOPIC_LINE_CONFIG: self.__configs.line_configs,
            self.TOPIC_FACTORY_CONFIG: self.__configs.factory_config,
            self.TOPIC_FACTORY_COMMANDS: self.__configs.factory_commands,

            self.TOPIC_MACHINE_STATUS: self.__status.machine_status,
            self.TOPIC_LINE_STATUS: self.__status.line_status
        }


        self.__client = mqtt.Client()
        self.__client.on_connect = self.__on_connect

        self.__client.message_callback_add(f"{self.__topic_start}/{self.TOPIC_LINE_CONFIG}/Set", self.__on_message_line_config_set)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.TOPIC_FACTORY_CONFIG}/Set", self.__on_message_factory_config_set)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.TOPIC_FACTORY_COMMANDS}/Set", self.__on_message_factory_command_set)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.TOPIC_WH_CONTENT}/Set", self.__on_message_wh_content_set)


        self.__client.message_callback_add(f"{self.__topic_start}/+/Get", self.__on_message_get)

        self.__client.on_message = self.__on_message_fallback

        self.__client.on_disconnect = self.__on_disconnect

        self.__client.connect(self.__BROKER_ADDR, self.__PORT)

        self.__client.loop_start()

# Methodes for mqtt config
###################################################################################################
    def disconnect(self):
        '''Disconnect from MQTT broker.'''
        self.__client.loop_stop()
        self.__client.disconnect()


    def __on_disconnect(self, client, userdata, rc):
        '''Disconnection callback.'''
        log.warning("Connection to MQTT-Broker disconnected")


    def __on_connect(self, client: mqtt.Client, _userdata, _flags, rc):
        '''Connection callback.
        
        Args:
            client(mqtt.Client): connection client.
        '''
        log.warning(f"Connected to MQTT-Broker. Result code: {rc}")

        client.subscribe("Debug")
        client.subscribe("Status")
        client.subscribe(f"{self.__topic_start}/+/Get")
        client.subscribe(f"{self.__topic_start}/+/Set")


    def __on_message_fallback(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new message that couldn't be filtered in other callbacks.'''

        log.warning(f"Message received for topic {msg.topic}: {msg.payload}")

# Methodes for receiving config or controls
###################################################################################################
    def __on_message_line_config_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the LineConfig topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg: dict = json.loads(msg.payload)
        log.warning(f"{msg.topic.removeprefix(self.__topic_start)}: {decoded_msg}")
        if self.__configs.line_configs.get(decoded_msg["name"]) == None:
            decoded_msg.update({"new": True})
        else:
            decoded_msg.update({"changed": True})
        self.__configs.line_configs.update({decoded_msg["name"]: decoded_msg})


    def __on_message_factory_config_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the FactoryConfig topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg = json.loads(msg.payload)
        log.warning(f"{msg.topic.removeprefix(self.__topic_start)}: {decoded_msg}")
        self.__configs.factory_config.update(decoded_msg)


    def __on_message_factory_command_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the FactoryCommand topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg = json.loads(msg.payload)
        log.warning(f"{msg.topic.removeprefix(self.__topic_start)}: {decoded_msg}")
        self.__configs.factory_commands.update(decoded_msg)


    def __on_message_wh_content_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the WHContent/Set topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg = json.loads(msg.payload)
        log.warning(f"{msg.topic.removeprefix(self.__topic_start)}: {decoded_msg}")
        try:
            with open(self.__wh_content_file, "r+") as fp:
                json_str = json.load(fp)
                json_str["content"] = decoded_msg
                fp.seek(0)
                json.dump(json_str, fp, indent=4)
                fp.truncate()
        except Exception as e:
            log.error(e)

# Methodes for sending Data or handling data requests
###################################################################################################
    def __on_message_get(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new get massage, gets the value for the given topic and publishes it.

        Args:
            msg: The received MQTTMessage.
        '''
        topic = msg.topic.removesuffix("/Get")
        topic_end = topic.removeprefix(f"{self.__topic_start}/")
        self.log.info(f"Get /{topic_end}/Data")
        if topic_end == self.TOPIC_WH_CONTENT:
            self.send_wh_content_data()
        else:
            try:
                data = self.__topics[topic_end]
            except Exception:
                data = f"ERROR: cant get data for topic: {topic}"
            try:
                self.__client.publish(f"{topic}/Data", json.dumps(data))
            except TypeError as e:
                self.log.error(f"Error for publish of {topic_end}/Data: {e}")


    def send_data(self, topic, data:str=None):
        '''Send data to given topic, if data==None default data for the given topic will be sent

        Args:
            topic: The topic of the data to send.
            data: The data to send, if None the default data for the given topic will be sent.
        '''
        self.log.info(f"Send {topic}/Data")
        if data == None:
            data = self.__topics[topic]
        self.__client.publish(f"{self.__topic_start}/{topic}/Data", json.dumps(data))


    def send_wh_content_data(self):
        '''Publishes the current wh_content.
        '''
        try:
            with open(self.__wh_content_file, "r") as fp:
                content = json.load(fp)["content"]
                self.__client.publish(f"{self.__topic_start}/{self.TOPIC_WH_CONTENT}/Data", json.dumps(content))
        except Exception as e:
            log.error(e)

if __name__ == "__main__":
    MqttHandler(factory_name="Right")
    input("Press Enter to end")