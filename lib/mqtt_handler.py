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


class MqttHandler():
    '''Handels Communication with mqtt broker.
    
    Attributes:
        configs (Configs): Object where all config data can be saved.
    '''

    __BROKER_ADDR = "192.168.0.59"
    __PORT = 1883

    __TOPIC_LINE_CONFIG = "LineConfig"
    __TOPIC_FACTORY_CONFIG = "FactoryConfig"
    __TOPIC_FACTORY_COMMANDS = "FactoryCommand"

    __TOPIC_WH_CONTENT = "WHContent"
    __TOPIC_MACHINES_STATUS = "MachinesStatus"
    __TOPIC_FACTORY_STATUS = "FactoryStatus"
    __TOPIC_lINE_STATUS = "LineStatus"
    
    

    def __init__(self, factory_name: str, states, configs: Configs) -> None:
        '''Init MqttInterface.
        
        Args:
            factory_name (str): Name of the factory (for example Right).
            states (State): Possible States of line.
            configs (Configs): Object where all config data can be saved.
        '''

        self.__BROKER_ADDR = "test.mosquitto.org"

        global log
        self.log = log.getChild(f"Mqtt")

        self.__topic_start = f"MiniFactory/{factory_name}/Factory"
        self.__wh_content_file = f"{factory_name.lower()}_wh_content.json"
        self.__states = states
        self.__configs = configs

        self.__topics = {
            self.__TOPIC_LINE_CONFIG: [f"{self.__topic_start}/{self.__TOPIC_LINE_CONFIG}", self.__configs.line_configs]
        }


        self.__client = mqtt.Client()
        self.__client.on_connect = self.__on_connect

        self.__client.message_callback_add(f"{self.__topic_start}/{self.__TOPIC_LINE_CONFIG}/Set", self.__on_message_line_config_set)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.__TOPIC_FACTORY_CONFIG}/Set", self.__on_message_factory_config_set)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.__TOPIC_FACTORY_COMMANDS}/Set", self.__on_message_factory_command_set)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.__TOPIC_WH_CONTENT}/Set", self.__on_message_wh_content_set)


        self.__client.message_callback_add(f"{self.__topic_start}/{self.__TOPIC_LINE_CONFIG}/Get", self.__on_message_line_config_get)
        self.__client.message_callback_add(f"{self.__topic_start}/{self.__TOPIC_WH_CONTENT}/Get", self.__on_message_wh_content_get)

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


    def __on_message_fallback(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new message that couldn't be filtered in other callbacks.'''

        log.warning(f"Message received for topic {msg.topic}: {msg.payload}")


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
        client.subscribe(f"{self.__topic_start}/{self.__TOPIC_LINE_CONFIG}/#")
        client.subscribe(f"{self.__topic_start}/{self.__TOPIC_FACTORY_CONFIG}")
        client.subscribe(f"{self.__topic_start}/{self.__TOPIC_FACTORY_COMMANDS}")
        client.subscribe(f"{self.__topic_start}/{self.__TOPIC_WH_CONTENT}")
        client.subscribe(f"{self.__topic_start}/{self.__TOPIC_WH_CONTENT}/Get")

# Methodes for receiving config or controls
###################################################################################################
    def __on_message_line_config_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the LineConfig topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        line_config: dict = json.loads(msg.payload)
        line_config = self.__convert_to_states(line_config)
        print(f"LineConfig/Set: {line_config}")
        if self.__configs.line_configs.get(line_config["name"]) == None:
            line_config.update({"new": True})
        else:
            line_config.update({"changed": True})
        self.__configs.line_configs.update({line_config["name"]: line_config})

    def __convert_to_states(self, config: dict) -> dict:
        '''Converts all the state names to actual states'''
        if config["start_at"].lower() == "start":
                config["start_at"] = "GR1"
        if config["start_at"].lower() == "storage":
            config["start_at"] = "WH_RETRIEVE"
        if config["end_at"].lower() == "storage":
            config["end_at"] = "WH_STORE"
        for state in self.__states:
            if state.name == config["start_at"]:
                config["start_at"] = state
            if state.name == config["end_at"]:
                config["end_at"] = state
            if type(config["start_at"]) != str and type(config["end_at"]) != str:
                break
        else:
            raise LookupError(f"Config {config['name']} could not be parsed.")
        
        return config


    def __on_message_factory_config_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the FactoryConfig topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg = json.loads(msg.payload)
        print(f"FactoryConfig/Set: {decoded_msg}")
        self.__configs.factory_config.update(decoded_msg)


    def __on_message_factory_command_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the FactoryCommand topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg = json.loads(msg.payload)
        print(f"FactoryCommand/Set: {decoded_msg}")
        self.__configs.factory_commands.update(decoded_msg)


    def __on_message_wh_content_set(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new massage under the WHContent/Set topic.
        
        Args:
            msg: The received MQTTMessage.
        '''
        decoded_msg = json.loads(msg.payload)
        print(f"WHContent/Set: {decoded_msg}")
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
    def __on_message_get_value(self, _client, _userdata, msg: mqtt.MQTTMessage):
        '''Callback for new get massage, gets the value for the given topic and publishes it.
        '''
        topic = msg.topic.removesuffix("/Get")
        print(f"Get {msg.topic}")
        self.__client.publish(f"{topic}/Data", json.dumps(self.__configs.line_configs))
        print(f"Published message to topic {topic}/Data")


    def __on_message_line_config_get(self, _client, _userdata, _msg):
        '''Callback for new massage under the LineConfig/Get topic.\n
        Publishes the current line_configs.
        '''
        print(f"Get LineConfig")
        self.__client.publish(f"{self.__topic_start}/{self.__TOPIC_LINE_CONFIG}/Data", json.dumps(self.__configs.line_configs))
        print(f"Published message to topic {self.__topic_start}/{self.__TOPIC_LINE_CONFIG}/Data")


    def __on_message_factory_config_get(self, _client, _userdata, _msg):
        '''Callback for new massage under the FactoryConfig/Get topic.\n
        Publishes the current factory_config.
        '''
        print(f"Get LineConfig")
        self.__client.publish(f"{self.__topic_start}/{self.__TOPIC_FACTORY_CONFIG}/Data", json.dumps(self.__configs.factory_config))
        print(f"Published message to topic {self.__topic_start}/{self.__TOPIC_FACTORY_CONFIG}/Data")


    def __on_message_factory_commands_get(self, _client, _userdata, _msg):
        '''Callback for new massage under the FactoryCommand/Get topic.\n
        Publishes the current factory_commands.
        '''
        print(f"Get FactoryCommands")
        self.__client.publish(f"{self.__topic_start}/{self.__TOPIC_FACTORY_COMMANDS}/Data", json.dumps(self.__configs.factory_commands))
        print(f"Published message to topic {self.__topic_start}/{self.__TOPIC_FACTORY_COMMANDS}/Data")


    def __on_message_wh_content_get(self, _client, _userdata, _msg):
        '''Callback for new massage under the WHContent/Get topic.\n
        Publishes the current wh_content.
        '''
        print(f"Get WHContent")
        try:
            with open(self.__wh_content_file, "r") as fp:
                content = json.load(fp)["content"]
                self.__client.publish(f"{self.__topic_start}/{self.__TOPIC_WH_CONTENT}/Data", json.dumps(content))
                print(f"Published message to topic {self.__topic_start}/{self.__TOPIC_WH_CONTENT}/Data")
        except Exception as e:
            log.error(e)




if __name__ == "__main__":
    MqttHandler(factory_name="Right")
    input("Press Enter to end")