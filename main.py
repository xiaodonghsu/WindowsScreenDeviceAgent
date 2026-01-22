import time
from common.config import load_config
from tb_client import ThingsBoardClient
from rpc_handler import handle_rpc
from system.device_status import get_device_status
from system.device_attr import get_device_attributes
from common.logger import setup_logger

# 初始化日志
logger = setup_logger("screen-agent")

cfg = load_config()

tb = ThingsBoardClient(
    cfg["thingsboard"]["host"],
    cfg["thingsboard"]["port"],
    cfg["thingsboard"]["access_token"]
)

logger.info(f"ThingsBoard客户端已连接到 {cfg['thingsboard']['host']}:{cfg['thingsboard']['port']}")

tb.send_attributes(get_device_attributes())
logger.info("设备属性已发送")

def on_message(client, userdata, msg):
    logger.info(f"收到消息，主题: {msg.topic}")
    handle_rpc(tb, msg)

tb.start(on_message)
logger.info("MQTT客户端已启动，开始监听RPC消息")

logger.info(f"设备状态监控已启动，心跳间隔: {cfg['device']['heartbeat_interval']}秒")
while True:
    try:
        tb.send_telemetry(get_device_status())
        logger.debug("设备遥测数据已发送")
    except Exception as e:
        logger.error(f"发送遥测数据失败: {e}")
    
    time.sleep(cfg["device"]["heartbeat_interval"])
