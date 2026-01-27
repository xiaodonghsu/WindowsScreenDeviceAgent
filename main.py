import time
from common import download_config, load_assets
from tb_client import ThingsBoardClient
from rpc_handler import handle_rpc
from system.device_status import get_device_status
from system.device_attr import get_device_attributes
from common.logger import setup_logger
from common import load_env, get_cms_token
# 读取参数

import argparse

# 根据命令行的参数从服务端获取配置信息
# 参数包括:
#  --cms_baseurl=192.168.41.135:8080
#  --cms_token="xxxx"
#  --device_name=screen-d16
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--cms_baseurl", help="CMS服务器地址", default="")
parser.add_argument("-n", "--device_name", help="设备名称", default="")
parser.add_argument("-t", "--cms_token", help="CMS服务器令牌", default="")

args = parser.parse_args()

# 初始化日志
logger = setup_logger("screen-agent")

# 从服务器下载配置
cms_baseurl = args.cms_baseurl
if cms_baseurl == "":
    cms_baseurl, _ = load_env()
if cms_baseurl == "":
    logger.error("未提供CMS服务器地址")
    exit(1)

device_name = args.device_name
if device_name == "":
    _, device_name = load_env()
if device_name == "":
    logger.error("未提供设备名称")
    exit(1)

cms_token = args.cms_token
if cms_token == "":
    cms_token = get_cms_token(cms_baseurl)
if cms_token == "":
    logger.error("未提供CMS服务器令牌")
    exit(1)

config  = download_config(cms_baseurl, device_name, cms_token)

if config is None:
    logger.error("下载配置失败")
    exit(1)

# 加载配置文件

tb = ThingsBoardClient(
    config["thingsboard"]["host"],
    config["thingsboard"]["port"],
    config["thingsboard"]["access_token"]
)

logger.info(f"ThingsBoard客户端已连接到 {config['thingsboard']['host']}:{config['thingsboard']['port']}")

tb.send_attributes(get_device_attributes())
logger.info("设备属性已发送")

def on_message(client, userdata, msg):
    logger.info(f"收到消息，主题: {msg.topic}")
    handle_rpc(tb, msg)

tb.start(on_message)
logger.info("MQTT客户端已启动，开始监听RPC消息")

logger.info(f"设备状态监控已启动，心跳间隔: {config['device']['heartbeat_interval']}秒")
while True:
    try:
        data=get_device_status()
        if data:
            tb.send_telemetry(data=data)
            logger.debug("设备遥测数据已发送")
        data=load_assets()
        if data:
            tb.send_telemetry(data=data)
            logger.debug("设备遥测数据已发送")
    except Exception as e:
        logger.error(f"发送遥测数据失败: {e}")
    
    time.sleep(config["device"]["heartbeat_interval"])
