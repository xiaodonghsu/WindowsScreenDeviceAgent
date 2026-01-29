# 测试脚本

## 获取TOKEN,CONFIG

python -c "from common import get_cms_token; print(get_cms_token())"

python -c "from common import download_config; import json; print(json.dumps(download_config(), indent=4))"

python -c "from common import download_assets; print(download_assets())"


## 测试浏览器功能

python -c "from player import open_url; open_url('https://www.baidu.com')"

## 测试幻灯片功能

python -c "from player.slide_player import get_status; print(get_status())"


python -c "from player.slide_player import play_slide; play_slide('C:\\Users\\胥晓冬\\OneDrive\\Exchange\\嘉环展厅控制方案\\ppt-test.pptx')"

python -c "from player.slide_player import next_page; next_page()"

python -c "from player.slide_player import prev_page; prev_page()"

python -c "from player.slide_player import stop_slide; stop_slide()"


## 测试 VLC 播放功能

python -c "from player.video_player import VLCRemote; vlc = VLCRemote(); vlc.play_video('D:\\Files\\Downloads\\xunjian.mp4')"


python -c "from player.video_player import VLCRemote; vlc = VLCRemote(); print(vlc.is_rc_alive())"

python -c "from player.video_player import VLCRemote; vlc = VLCRemote(); print(vlc.get_status())"

python -c "from player.video_player import VLCRemote; vlc = VLCRemote(); print(vlc.is_running())"

python -c "from player.video_player import VLCRemote; vlc = VLCRemote(); print(vlc.get_playlist())"


## 测试功能

python -c "from system.monitor import get_running_processes; print(get_running_processes())"

python -c "from system.monitor import get_slide_player_status; print(get_slide_player_status())"

python -c "from system.device_status import get_network_status; print(get_network_status())"

## MQTT 测试


## RPC 测试
THINGSBOARD_TOKEN="Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ4eGRAYmVzdGxpbmsuY29tLmNuIiwidXNlcklkIjoiZjRjYTljNDAtZjBmOC0xMWYwLWJkZDMtYjcxM2JhNjVkM2MwIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJzZXNzaW9uSWQiOiIzZWVjOGY0OC0wMDNlLTRiNTMtOWU0Yy1kODYzMTdmMTFjMzMiLCJleHAiOjE3Njg5NjQ0MDUsImlzcyI6InRoaW5nc2JvYXJkLmlvIiwiaWF0IjoxNzY4OTU1NDA1LCJmaXJzdE5hbWUiOiLmmZPlhqwiLCJsYXN0TmFtZSI6IuiDpSIsImVuYWJsZWQiOnRydWUsImlzUHVibGljIjpmYWxzZSwidGVuYW50SWQiOiJhMzhhMjI2MC1mMGY4LTExZjAtYmRkMy1iNzEzYmE2NWQzYzAiLCJjdXN0b21lcklkIjoiMTM4MTQwMDAtMWRkMi0xMWIyLTgwODAtODA4MDgwODA4MDgwIn0.14Q8W1gMbOTohwUrelaj2j2Ivqi7qpEp-aCEBSAJvCWxp4RGKuwZe_zxWsZNrYAPiT-cNvYKuZ-7xUBQlGTcHw"

THINGSBOARD_DEVICEID=576fc550-f117-11f0-bdd3-b713ba65d3c0

curl --location "http://nuc10.i.uassist.cn:8080/api/plugins/rpc/oneway/${THINGSBOARD_DEVICEID}" ^
--header "Content-Type: application/json" ^
--header "Authorization: ${THINGSBOARD_TOKEN}" ^
--data "{  ^
    ""id"": 1,  ^
    ""method"": ""play_ppt"",  ^
    ""params"": {  ^
        ""url"": ""test-ppt.pptx"",  ^
        ""startPage"": 1  ^
    } ^
}"


## 公网 RPC 测试

### device openeuler

mosquitto_sub -h 106.14.186.252 -p 59145 -u b2tYLGnXbHUP8Gm2fWrR -t "v1/devices/me/rpc/request/+" -v -d

mosquitto_sub -h 106.14.186.252 -p 59145 -u b2tYLGnXbHUP8Gm2fWrR -t "v1/devices/me/attributes" -v -d



### 内网模式


mosquitto_sub -h 192.168.41.135 -p 1883 -u b2tYLGnXbHUP8Gm2fWrR -t "v1/devices/me/rpc/request/+" -v -d

### shell 测试

mosquitto_sub -h 106.14.186.252 -p 59145 -u b2tYLGnXbHUP8Gm2fWrR -t "v1/devices/me/rpc/request/+" -v | while read -r topic payload; do
    echo "收到命令: $payload"
    
    # 执行命令并捕获输出
    result=$(eval "$payload" 2>&1)
    exit_code=$?
    
    # 构建响应消息
    response="{
        \"command\": \"$payload\",
        \"output\": \"$(echo $result | sed 's/\"/\\"/g')\",
        \"exit_code\": $exit_code,
        \"timestamp\": \"$(date -Iseconds)\"
    }"
    
    # 发布结果
    mosquitto_pub -h $BROKER -p $PORT -t "$RESPONSE_TOPIC" -m "$response"
    echo "已发送响应: $response"
done


