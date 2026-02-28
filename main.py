import sys
import win32api
import win32event
import winerror

# 防止重复启动 - 使用 Windows Mutex
mutex = None

try:
    mutex_name = "Global\\ExpoAgent_SingleInstance_Mutex"
    mutex = win32event.CreateMutex(None, False, mutex_name)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        print("ExpoAgent 已经在运行中，请勿重复启动")
        sys.exit(1)
except Exception as e:
    print(f"创建单实例锁失败: {e}")

from math import log
from nt import scandir
import time
from tkinter import N
from cms import download_config, download_programs, load_program
from cms.program import download_cms_scene_name
from common.config import get_device_name
from iot import ThingsBoardClient
from iot.handler import handle_rpc, handle_attributes
from player import slide_player
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
    logger.error("未提供设备名称, 请设置.env或设置环境变量: IOT_DEVICE_NAME")
    sys.exit(1)
else:
    # 初始化日志
    logger = setup_logger(device_name)

logger.info(f"本地设备名称: {device_name}")

# 获取服务器配置
cms_baseurl = args.cms_baseurl
if cms_baseurl == "":
    cms_baseurl = get_cms_baseurl()
logger.info(f"CMS服务器地址: {cms_baseurl}")
if cms_baseurl == "":
    logger.error("未提供CMS API地址, 请设置.env或设置环境变量 CMS_BASEURL")
    sys.exit(1)

# 从参数获取令牌
cms_token = args.cms_token
if cms_token == "":
    cms_token = get_cms_token(cms_baseurl)
# 尝试从服务器下载令牌
if cms_token == "":
    logger.error("未查询到CMS服务令牌,检查CMS服务器中的配置")
    sys.exit(1)

# 循环过程, 保证配置文件下载成功, 且能够正常连接到ThingsBoard
# 1. 从服务器下载配置
# 2. 连接ThingsBoard
while True:
    config  = download_config(cms_baseurl, device_name, cms_token)

    if config is None:
        logger.error("下载配置失败")
    else:
        logger.info(f"下载配置成功: {config}")
        # 加载配置文件,连接ThingsBoard

        iot_host = config["iot_host"]
        iot_port = config["iot_port"]
        device_token = config["iot_device_token"]

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
    logger.info(f"5秒后重试")
    time.sleep(5)

# 到这里的时候设备已经联网,开始正式工作

logger.info("发送设备属性")
tb.send_attributes(get_device_attributes())

# 端侧的核心工作: 监听服务端的消息, 处理一些TOPIC
def on_message(client, userdata, msg):
    logger.info(f"收到消息，主题: {msg.topic}, 负载: {msg.payload.decode("utf-8")}")
    if msg.topic.find("/rpc") > 0:
        logger.info(f"收到RPC消息")
        handle_rpc(tb, msg)
    elif msg.topic.find("/attributes") > 0:
        logger.info(f"收到属性消息")
        handle_attributes(tb, msg)
    else:
        logger.info(f"未知消息，主题: {msg.topic}")

tb.start(on_message)
logger.info("已启动 MQTT 客户端监听消息")

logger.info("请求共享参数场景")
tb.request_shared_attributes(["scene"])

# scene_name = download_cms_scene_name()
# logger.info(f"获取到的场景名称: {scene_name}")

# if scene_name is None:
#     scene_name = "default"
# logger.info(f"设置激活场景: {scene_name}")
# tb.send_attributes({"scene": scene_name})

heartbeat_interval = config['iot_heartbeat_interval']
logger.info(f"启动设备状态周期上报，心跳间隔: {heartbeat_interval}秒")
assets = {}
player_staus = {"video_player": {},"web_player": {},"slide_player":{}}
while True:
    try:
        # 周期性例程: 更新设备参数
        data=get_device_status()
        if data:
            tb.send_telemetry(data=data)
            logger.debug("设备遥测数据已发送")
        # 选择性更新的参数
        # video_player
        from player import get_video_player_status
        status = get_video_player_status()
        if status:
            if not player_staus["video_player"] == status:
                tb.send_telemetry(data={"video_player": status})
                player_staus["video_player"] = status
        # web_player
        from player import get_web_player_status
        status = get_web_player_status()
        if status:
            if not player_staus["web_player"] == status:
                tb.send_telemetry(data={"web_player": status})
                player_staus["web_player"] = status
        # slide_player
        from player import get_slide_player_status
        status = get_slide_player_status()
        if status:
            if not player_staus["slide_player"] == status:
                tb.send_telemetry(data={"slide_player": status})
                player_staus["slide_player"] = status
    except Exception as e:
        logger.error(f"发送遥测数据失败: {e}")

    time.sleep(heartbeat_interval)
