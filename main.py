import yaml
import time
from tb_client import ThingsBoardClient
from rpc_handler import handle_rpc
from system.monitor import collect_status
from system.device_info import get_device_attributes

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
    tb.send_telemetry(collect_status())
    time.sleep(cfg["device"]["heartbeat_interval"])
