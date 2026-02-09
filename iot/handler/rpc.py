from logging import Logger


import json
import player
import logging
from common.config import get_device_name
logger: Logger = logging.getLogger(get_device_name())

def handle_rpc(tb_client, msg):
    topic = msg.topic
    request_id = topic.split("/")[-1]
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        logger.error(f"解析RPC负载失败: {e}")
        return None

    logger.info(f"RPC请求内容: {json.dumps(payload)}")
    method = payload.get("method")
    params = payload.get("params", {})

    try:
        # 从模块中动态获取函数
        func = None
        if hasattr(player, method):
            func = getattr(player, method)
        if func is None:
            logger.warning(f"未知的RPC方法: {method}")
            return None

        # 调用函数
        if params:
            func(**params)
        else:
            func()

        tb_client.reply_rpc(request_id, {"result": "ok"})
    except Exception as e:
        logger.error(f"RPC方法调用失败: {e}")
        tb_client.reply_rpc(request_id, {"error": str(e)})

