# 测试脚本

## 测试浏览器功能

python -c "from player.web_player import open_url; open_url('https://www.baidu.com')"

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

