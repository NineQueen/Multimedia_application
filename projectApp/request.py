import paho.mqtt.client as mqtt
from .models import Information
import json

mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/request-A09"
mqtt_client = mqtt.Client("Request-Zhuv2")
mqtt_client.connect(mqtt_broker, mqtt_port)
mqtt_client.subscribe(mqtt_topic, mqtt_qos)

def mqtt_on_message(client, userdata, message):
    try:
        d_msg = str(message.payload.decode("utf-8"))
        print("get message",d_msg)
        iotData = json.loads(d_msg)
        if type(iotData['count']) == int:
            locations = Information.objects.values_list('loc', flat = True).distinct().order_by('loc')
            pos = iotData['count'] % len(locations)
            latest_data = Information.objects.filter(loc = locations[pos]).latest('date_created')
            response = {
                "node_id" : latest_data.node_id,
                "loc" : latest_data.loc,
                "temp" : str(latest_data.temp),
                "hum" : str(latest_data.hum),
                "light" : str(latest_data.light),
                "snd" : str(latest_data.snd)
            }
            mqtt_client.publish(mqtt_topic, json.dumps(response))
    except BaseException as e:
        print("Error! {}".format(e))

mqtt_client.on_message = mqtt_on_message
mqtt_client.loop_start()