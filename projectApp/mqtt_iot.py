import paho.mqtt.client as mqtt
from .models import Information,WarningMessage,Warning,Event
import json
from django.utils import timezone
from .function import AlertClassifier
ID = "A09"
mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/sensor-A"
def check_empty(loc,time):
    event = Event.objects.filter(loc = loc)
    event = event.filter(begin_time__lte = time)
    event = event.filter(end_time__gte = time)
    return event

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
        time = timezone.now()
        event = check_empty(p.loc,time)
        empty = False
        if len(event) == 0:
            empty = True
        res = AlertClassifier(p.temp,p.hum,p.light,p.snd,empty)
        # if res["type"]:
        #     warning_message = WarningMessage(information = p,message = res["message"])
            
        print("save")
    except Exception as e:
        print("Error! {}".format(e))
mqtt_client = mqtt.Client("Web-Zhuv2")
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker,mqtt_port)
print("Connect")
mqtt_client.subscribe(mqtt_topic,mqtt_qos)
mqtt_client.loop_start()