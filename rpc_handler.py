import json
import player

def handle_rpc(tb_client, msg):
    topic = msg.topic
    request_id = topic.split("/")[-1]
    payload = json.loads(msg.payload.decode())

    print(payload)

    method = payload.get("method")
    params = payload.get("params", {})

    try:
        # 从模块中动态获取函数
        func = None
        if hasattr(player, method):
            func = getattr(player, method)
        if func is None:
            raise Exception(f"未知的RPC方法: {method}")
        
        # 调用函数
        if params:
            func(**params)
        else:
            func()

        tb_client.reply_rpc(request_id, {"result": "ok"})
    except Exception as e:
        tb_client.reply_rpc(request_id, {"error": str(e)})
