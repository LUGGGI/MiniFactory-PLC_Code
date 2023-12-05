import paho.mqtt.client as mqtt

mqttBroker = "192.168.0.59"
port = 1883

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    zahl = str(input("Bitte gib eine Zahl ein: "))
    client.publish("3DRobot1", zahl)
    print("Just published " + str(zahl) + " to topic GetStatus")

    client.disconnect()

client = mqtt.Client("Test2")
client.on_connect = on_connect

client.connect(mqttBroker, port)
client.loop_forever()
