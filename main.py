from math import log
import time
from cms import download_config, download_assets, load_assets
from common import load_config, get_device_name
from iot import ThingsBoardClient
from iot.handler import handle_rpc, handle_attributes
from system.device_status import get_device_status
from system.device_attr import get_device_attributes
from common.logger import setup_logger
from cms import get_cms_token, get_cms_baseurl
# 读取参数

import argparse

# 根据命令行的参数从服务端获取配置信息
# 参数包括:
#  --cms_baseurl=http://192.168.41.135:1337/api
#  --cms_token="xxxx"
#  --device_name=screen-d16
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--device_name", help="设备名称", default="")
parser.add_argument("-s", "--cms_baseurl", help="CMS服务器地址", default="")
parser.add_argument("-t", "--cms_token", help="CMS服务器令牌", default="")

args = parser.parse_args()

# 提取设备名称
device_name = args.device_name
if device_name == "":
    device_name = get_device_name()
if device_name == "":
    # 初始化日志
    logger = setup_logger(__name__)
    logger.error("未提供设备名称, 可以在环境变量中设置: IOT_DEVICE_NAME")
    exit(1)
else:
    # 初始化日志
    logger = setup_logger(device_name)

# 从服务器下载配置
cms_baseurl = args.cms_baseurl
if cms_baseurl == "":
    cms_baseurl = get_cms_baseurl()
if cms_baseurl == "":
    logger.error("未提供CMS API地址, 可以在环境变量中设置 CMS_BASEURL")
    exit(1)

# 从服务器下载令牌
cms_token = args.cms_token
if cms_token == "":
    cms_token = get_cms_token(cms_baseurl)
if cms_token == "":
    logger.error("未查询到CMS服务令牌,检查CMS服务器中的配置")
    exit(1)

config  = download_config(cms_baseurl, device_name, cms_token)

if config is None:
    logger.error("下载配置失败")
    exit(1)

# 加载配置文件,连接ThingsBoard

iot_host = config["iot_host"]
iot_port = config["iot_port"]
device_token = config["iot_device_token"]
while True:
    try:
        tb = ThingsBoardClient(
            host=iot_host,
            port=iot_port,
            token=device_token 
        )
        logger.info(f"ThingsBoard客户端已连接到 {iot_host}:{iot_port}")
        break
    except Exception as e:
        logger.error(f"连接到ThingsBoard {iot_host}:{iot_port} 失败: {e}")
        time.sleep(1)

logger.info("发送设备属性")
tb.send_attributes(get_device_attributes())

logger.info("启动 MQTT 客户端监听消息")
def on_message(client, userdata, msg):
    logger.info(f"收到消息，主题: {msg.topic}, 负载: {msg.payload}")
    if msg.topic.endswith("/rpc"):
        handle_rpc(tb, msg)
    elif "/attributes" in msg.topic:
        handle_attributes(tb, msg)
    else:
        logger.info(f"未知消息，主题: {msg.topic}")

tb.start(on_message)

# logger.info("请求场景")
tb.request_attributes(["scene"])

# 循环0.1秒 * 30次，读取场景
loop_count = 0
scene = "default"
while True:
    time.sleep(0.1)
    if "scene" in tb.attributes:
        scene = tb.attributes["scene"]
        break
    if loop_count > 30:
        logger.error("场景请求超时")
        break
    loop_count += 1

logger.info(f"场景: {scene}, 开始下载资源数据")

# 下载场景-资源数据
scene_assets = download_assets(scene_name=scene)

if scene_assets is None:
    logger.error(f"场景: {scene}, 未适配到合适的资源数据.")
    if scene != "default":
        scene_assets = download_assets(scene_name="default")
        if scene_assets is None:
            logger.error(f"场景: {scene}, 未适配到合适的资源数据.")

if not scene_assets is None:
    logger.info(f"适配到的资源数据: {scene_assets}.")

heartbeat_interval = config['config']['device']['heartbeat_interval']
logger.info(f"设备状态监控已启动，心跳间隔: {heartbeat_interval}秒")
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

    time.sleep(heartbeat_interval)
