import paho.mqtt.client as mqtt
from .models import Information,WarningMessage,Warning,Event
import json
from django.utils import timezone
from .function import AlertClassifier
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


def send_custom_email(
    subject,
    to_emails,
    text_content=None,
    html_content=None,
    from_email=None,
    template_name=None,
    context=None,
    fail_silently=False
):
    print("check email")
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    # 默认发件人
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    # 如果提供了模板，则渲染 HTML 内容
    if template_name and context:
        html_content = render_to_string(template_name, context)

    try:
        # 如果同时有文本和 HTML 内容，发送多部分邮件
        if html_content and text_content:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_emails
            )
            msg.attach_alternative(html_content, "text/html")
            return msg.send(fail_silently=fail_silently)

        # 如果只有 HTML 内容，也发送为多部分邮件（包含一个简单的文本替代）
        elif html_content:
            msg = EmailMultiAlternatives(
                subject=subject,
                body="这是一封HTML格式的邮件,请使用支持HTML的邮件客户端查看。",
                from_email=from_email,
                to=to_emails
            )
            msg.attach_alternative(html_content, "text/html")
            return msg.send(fail_silently=fail_silently)

        # 只有文本内容
        else:
            print("check")
            return send_mail(
                subject=subject,
                message=text_content,
                from_email=from_email,
                recipient_list=to_emails,
                fail_silently=fail_silently
            )
    except Exception as e:
        logger.error(f"邮件发送失败: {str(e)}")
        if not fail_silently:
            raise
        return 0
ID = "A09"
mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/test-A"
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
        empty = 1
        if len(event) == 0:
            empty = 0
        res = AlertClassifier(p.temp,p.hum,p.light,p.snd,empty)
        if res["type"]:
            print("check error")
            context = {
                'room_value': p.loc,
                'time_value': p.date_created,
                'value': p,
                'Type': res["message"]
            }
            send_custom_email(
                subject="⚠️ Warning detected",
                to_emails=["owen.zhx@outlook.com"],
                template_name="projectApp/alert_email.html",  # 替换为实际的模板路径
                context=context
            )
            warning_message = WarningMessage(information = p,message = res["message"])
            warning_message.save()
            warning_loc = Warning.objects.filter(loc = p.loc).filter(status = False)
            if len(warning_loc) == 0:
                print("create warning")
                warning = Warning(loc = p.loc,status = False)
                warning.save()
                warning.message.add(warning_message)
            else:
                warning_loc = warning_loc[0]
                warning_loc.message.add(warning_message)
        print("save")
    except Exception as e:
        print("Error! {}".format(e))
mqtt_client = mqtt.Client("Web-Zhuv2")
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker,mqtt_port)
print("Connect")
mqtt_client.subscribe(mqtt_topic,mqtt_qos)
mqtt_client.loop_start()