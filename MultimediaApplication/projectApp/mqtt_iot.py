import paho.mqtt.client as mqtt
from .models import Information
import json

ID = "A09"
mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/sensor-A09"
def mqtt_on_message(client, userdata,msg):
    try:
        d_msg = str(msg.payload.decode("utf-8"))
        iotData = json.loads(d_msg)
        print("Received message on topic %s : %s" % (msg.topic, iotData))
        p = Information(
            node_id = iotData["node_id"],
            loc = iotData["loc"].upper(),
            temp = iotData["temp"],
            hum = iotData["hum"],
            light = iotData["light"],
            snd = iotData["snd"]
            )
        print("check")
        p.save()
    except BaseException as e:
        print("Error! {}".format(e))
mqtt_client = mqtt.Client("Web-A09")
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker,mqtt_port)
print("Connect")
mqtt_client.subscribe(mqtt_topic,mqtt_qos)
mqtt_client.loop_start()