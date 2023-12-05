import paho.mqtt.client as mqtt

broker_address = "192.168.0.59"
port = 1883

def on_connect(client, userdata, flags, rc):
    print("Verbunden mit dem MQTT-Broker. Rückgabewert: " + str(rc))

    client.subscribe("Status")
    client.subscribe("Parts")
    client.subscribe("Produced")
    client.subscribe("Workload")
    client.subscribe("ChangedStatus")
    client.subscribe("3DRobot1")
    client.subscribe("3DRobot2")
    client.subscribe("3DRobot3")
    client.subscribe("Vacuumgripper")
    client.subscribe("Multi")
    client.subscribe("Assembly")
    client.subscribe("Warehouse")
    client.subscribe("Punching")


def on_message(client, userdata, msg):
    nachricht_string = msg.payload.decode('utf-8')
    print("Nachricht empfangen: " + msg.topic + " " + nachricht_string)
    topic = msg.topic

def on_disconnect(client, userdata, rc):
    print("Verbindung zum MQTT-Broker getrennt")

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

client.connect(broker_address, port)

client.loop_forever()
