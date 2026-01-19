import yaml
import time
from tb_client import ThingsBoardClient
from rpc_handler import handle_rpc
from system.device_status import get_device_status
from system.device_attr import get_device_attributes

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

tb = ThingsBoardClient(
    cfg["thingsboard"]["host"],
    cfg["thingsboard"]["port"],
    cfg["thingsboard"]["access_token"]
)

tb.send_attributes(get_device_attributes())

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload}")
    handle_rpc(tb, msg)

tb.start(on_message)

while True:
    tb.send_telemetry(get_device_status())
    time.sleep(cfg["device"]["heartbeat_interval"])
