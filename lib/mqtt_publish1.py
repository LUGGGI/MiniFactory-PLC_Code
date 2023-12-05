import paho.mqtt.client as mqtt
from random import randrange, uniform
import time

mqttBroker ="192.168.0.59"
port = 1883

client = mqtt.Client("Test1")
client.connect(mqttBroker,port)

while True:
    Number = 5
    client.publish("ChangedStatus", Number)
    print("Just published " + str(Number) + " to topic Test")
    time.sleep(1)
