import json
import paho.mqtt.client as mqtt
from random import randrange, uniform
import time

mqttBroker ="192.168.0.59"
# mqttBroker ="test.mosquitto.org"
port = 1883


topic_start = f"MiniFactory/Right/Factory"
topic_line_config = f"{topic_start}/LineConfig"
topic_factory_config = f"{topic_start}/FactoryConfig"
topic_factory_command = f"{topic_start}/FactoryCommand"

client = mqtt.Client("Sender")
client.connect(mqttBroker,port)

line_config = {
    "name": "Main1", 
    "run": True,
    "start_at": "start",
    "end_at": "END",
    "with_oven": True,
    "with_saw": True,
    "with_PM": False,
    "with_WH": False,
    "color": "WHITE"
}

factory_config = {
    "exit_if_end": True
}

factory_command = {
    "run": True,
    "stop": False
}

while True:
    client.publish(topic_line_config, json.dumps(line_config))
    print(f"Just published message to topic {topic_line_config}")
    time.sleep(1)
    client.publish(topic_factory_config, json.dumps(factory_config))
    print(f"Just published message to topic {topic_factory_config}")
    time.sleep(1)
    client.publish(topic_factory_command, json.dumps(factory_command))
    print(f"Just published message to topic {topic_factory_command}")
    time.sleep(1)
