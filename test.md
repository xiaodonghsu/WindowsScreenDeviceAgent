# 测试脚本

## 测试浏览器功能

python -c "from player.web_player import open_url; open_url('https://www.baidu.com')"

## 测试 VLC 播放功能

python -c "from player.video_player import VLCController; vlc = VLCController(); vlc.play_video('D:\\Files\\Downloads\\xunjian.mp4')"
