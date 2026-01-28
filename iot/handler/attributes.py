import json
import logging
logger = logging.getLogger(__name__)

def handle_attributes(tb_client, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
    except Exception as e:
        logger.error(f"解析消息失败: {e}. 消息: {msg.payload}")
        return
    if topic.endswith("attributes"):
        logger.info(f"收到属性变更消息: {payload}")
            # 如果是场景变更
        if "scene" in payload:
            scene = payload["scene"]
            logger.info(f"场景变更: {scene}")
            # TODO: 处理场景变更逻辑
    elif topic.find("attributes/response") > 0:
        logger.info(f"收到属性请求响应消息: {payload}")
        for attr_type in payload:
            for key in payload[attr_type]:
                value = payload[attr_type][key]
                logger.info(f"设置属性: {key} = {value}")
                tb_client.attributes[key] = value
    else:
        logger.warning(f"未知的属性消息: {payload}")
