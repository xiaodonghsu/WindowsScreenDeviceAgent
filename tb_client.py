import json
import paho.mqtt.client as mqtt

class ThingsBoardClient:
    def __init__(self, host, port, token):
        self.client = mqtt.Client()
        self.client.username_pw_set(token)
        self.client.connect(host, port, 60)

    def start(self, on_message):
        self.client.on_message = on_message
        self.client.subscribe("v1/devices/me/rpc/request/+")
        self.client.loop_start()

    def send_telemetry(self, data: dict):
        self.client.publish(
            "v1/devices/me/telemetry",
            json.dumps(data)
        )

    def send_attributes(self, data: dict):
        self.client.publish(
            "v1/devices/me/attributes",
            json.dumps(data)
        )

    def reply_rpc(self, request_id, payload):
        self.client.publish(
            f"v1/devices/me/rpc/response/{request_id}",
            json.dumps(payload)
        )
