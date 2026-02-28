import json
import logging

from cms.program import download_programs
from common.config import get_device_name
from player import play_program
logger = logging.getLogger(get_device_name())

def handle_attributes(tb_client, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
    except Exception as e:
        logger.error(f"解析消息失败: {e}. 消息: {msg.payload}")
        return None
    if topic.endswith("attributes"):
        logger.info(f"收到属性变更消息: {payload}")
            # 如果是场景变更
        if "scene" in payload:
            scene = payload["scene"]
            if tb_client.attributes.get("scene", "") != scene:
                # 处理场景变更逻辑
                logger.info(f"处理场景变更: {scene}")
                update_device_scene_program(tb_client=tb_client, scene=scene)
                # logger.info(f"设置属性: {"scene"} = {scene}")
                # tb_client.attributes["scene"] = scene
            else:
                logger.info(f"场景未变更: {scene}")
        else:
            logger.warning(f"未知的属性变更消息: {payload}")
    elif topic.find("attributes/response") > 0:
        logger.info(f"收到属性请求响应消息: {payload}")
        for attr_type in payload:
            for key in payload[attr_type]:
                value = payload[attr_type][key]
                if key == "scene":
                    update_device_scene_program(tb_client=tb_client, scene=value)
                else:
                    logger.info(f"设置属性: {key} = {value}")
                    tb_client.attributes[key] = value
    else:
        logger.warning(f"未知的属性消息: {payload}")


def update_device_scene_program(tb_client, scene: str):
    '''
    更新场景
    '''
    if tb_client.attributes.get("scene", "") != scene:
        programs = None
        for device_name in ["", "default"]:
            for scene_name in [scene, "default"]:
                logger.info(f"场景: {scene_name}, 尝试下载资源数据")
                # 下载场景-资源数据
                programs = download_programs(device_name=device_name, scene_name=scene_name)
                logger.info(f"节目单: {programs}")
                if len(programs["programs"]) == 0:
                    logger.warning(f"场景: {scene_name}, CMS未适配到合适的资源数据!")
                else:
                    logger.info(f"场景: {scene_name}, 适配到的资源数据: {programs}.")
                    tb_client.send_telemetry(programs)
                    break
                # default 只查询一次
                if scene_name == "default":
                    break
        logger.info(f"设置属性: {"scene"} = {scene}")
        tb_client.attributes["scene"] = scene
        # 根据情况自动进入第一个节目!
        play_program(0, start_pause=True)