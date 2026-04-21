import json
import paho.mqtt.client as mqtt
import time
import logging

from common.config import get_device_name
logger = logging.getLogger(get_device_name())

class ThingsBoardClient:
    def __init__(self, host, port, token):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(token)
        self.client.connect(host, port, 60)
        self.attributes = {}
        self._req_id = 1
        self._pending_req: Dict[int, float] = {}  # req_id -> time

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("连接ThingsBoard成功, 订阅主题...")
            self.client.subscribe("v1/devices/me/rpc/request/+")
            self.client.subscribe("v1/devices/me/attributes")
        else:
            logger.error(f"连接失败，代码: {rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.info(f"ThingsBoard连接断开, 代码: {rc}")
        if rc != 0:
            logger.error("异常断开，自动重连机制已触发...")
            # 库的自动重连已配置，此处也可添加自定义日志或状态更新
        # 注意：如果clean_session=False，重连后会自动恢复会话，无需手动重订阅

    def start(self, on_message):
        self.client.on_message = on_message
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
