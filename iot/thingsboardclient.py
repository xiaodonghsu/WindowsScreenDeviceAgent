import json
import paho.mqtt.client as mqtt
import time

class ThingsBoardClient:
    def __init__(self, host, port, token):
        self.client = mqtt.Client()
        self.client.username_pw_set(token)
        self.client.connect(host, port, 60)
        self.attributes = {}
        self._req_id = 1
        self._pending_req: Dict[int, float] = {}  # req_id -> time

    def start(self, on_message):
        self.client.on_message = on_message
        self.client.subscribe("v1/devices/me/rpc/request/+")
        self.client.subscribe("v1/devices/me/attributes")
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

    def request_shared_attributes(self, keys: dict):
        req_id = self._req_id
        self._req_id += 1
        topic = f"v1/devices/me/attributes/request/{req_id}"
        payload = json.dumps({"sharedKeys": ",".join(keys)}, ensure_ascii=False)
        self._pending_req[req_id] = time.time()
        self.client.publish(topic, payload)
        return req_id

    def reply_rpc(self, request_id, payload):
        self.client.publish(
            f"v1/devices/me/rpc/response/{request_id}",
            json.dumps(payload)
        )
