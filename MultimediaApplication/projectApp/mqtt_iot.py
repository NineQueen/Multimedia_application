import paho.mqtt.client as mqtt
from .models import Information
import json

ID = "A09"
mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/sensor-A"
def mqtt_on_message(client, userdata,msg):
    try:
        d_msg = str(msg.payload.decode("utf-8"))
        iotData = json.loads(d_msg)
        print("Received message on topic %s : %s" % (msg.topic, iotData))
        if float(iotData["hum"])  <= 0 or float(iotData["light"]) <= 0 or int(iotData["snd"])+80 <= 0:
            raise AssertionError("Smaller than 0!")
        if float(iotData["light"]) >= 100 or float(iotData["hum"]) >= 100:
            raise AssertionError("Greater than 100!")
        p = Information(
            node_id = iotData["node_id"],
            loc = iotData["loc"].upper(),
            temp = float(iotData["temp"]),
            hum = float(iotData["hum"]),
            light = int(iotData["light"]),
            snd = int(iotData["snd"])+80
            )
        p.save()
        print("save")
    except Exception as e:
        print("Error! {}".format(e))
mqtt_client = mqtt.Client("Web-24099372d")
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker,mqtt_port)
print("Connect")
mqtt_client.subscribe(mqtt_topic,mqtt_qos)
mqtt_client.loop_start()