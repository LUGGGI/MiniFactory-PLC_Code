import json
import paho.mqtt.client as mqtt
import time


mqttBroker ="192.168.0.59"
mqttBroker ="test.mosquitto.org"
port = 1883


topic_start = f"MiniFactory/Right/Factory"
topic_line_config_set = f"{topic_start}/LineConfig/Set"
topic_factory_config_set = f"{topic_start}/FactoryConfig/Set"
topic_factory_command_set = f"{topic_start}/FactoryCommand/Set"
topic_wh_content_set = f"{topic_start}/WHContent/Set"

topic_wh_content_get = f"{topic_start}/WHContent/Get"
topic_line_config_get = f"{topic_start}/LineConfig/Get"

client = mqtt.Client("Sender")
client.connect(mqttBroker,port)

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
            "Empty",
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

while True:
    if read == False:
        time.sleep(1)
        continue
    for config in line_configs:
        client.publish(topic_line_config_set, json.dumps(config))
        print(f"Just published message to topic {topic_line_config_set}")
        break
    # time.sleep(1)
    # client.publish(topic_factory_config, json.dumps(factory_config))
    # print(f"Just published message to topic {topic_factory_config}")
    # time.sleep(1)
    client.publish(topic_factory_command_set, json.dumps(factory_command))
    print(f"Just published message to topic {topic_factory_command_set}")
    # time.sleep(1)
    # client.publish(topic_wh_content_set, json.dumps(wh_content))
    # print(f"Just published message to topic {topic_wh_content_set}")
    # client.publish(topic_wh_content_get)
    # print(f"Just published message to topic {topic_wh_content_get}")
    # client.publish(topic_line_config_get)
    # print(f"Just published message to topic {topic_line_config_get}")
    # time.sleep(1)

    break
