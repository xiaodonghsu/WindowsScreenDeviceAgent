import json
from player.slide_player import play_ppt, next_page, prev_page
from player.video_player import play_video, stop_video
from player.web_player import open_url

def handle_rpc(tb_client, msg):
    topic = msg.topic
    request_id = topic.split("/")[-1]
    payload = json.loads(msg.payload.decode())

    print(payload)

    method = payload.get("method")
    params = payload.get("params", {})

    try:
        if method == "play_ppt":
            play_ppt(params["url"], params.get("startPage", 1))
        elif method == "next":
            next_page()
        elif method == "prev":
            prev_page()
        elif method == "play_video":
            play_video(params["url"])
        elif method == "open_url":
            open_url(params["url"])
        elif method == "stop":
            stop_video()
        else:
            raise Exception("Unknown RPC method")

        tb_client.reply_rpc(request_id, {"result": "ok"})
    except Exception as e:
        tb_client.reply_rpc(request_id, {"error": str(e)})
