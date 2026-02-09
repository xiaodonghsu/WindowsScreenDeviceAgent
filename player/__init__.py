'''
# 设计规范

## 动作支持列表

说明：

所有的动作应该以: Action_ Object 形式

包括:
### web 浏览器 支持的动作:
open_url(url)

### slide 幻灯片 支持的动作:
play_slide(url, start_page=1)
next_page()
prev_page()
stop_slide()

### video 视频播放器 支持的动作:

play_video(url, start_time=0)
forward_video(seconds=10)
backward_video(seconds=10)
stop_video()

### avatar 数字人播放器 支持的动作:

play_avatar(playlist)
show_text(text, duration=1)
stop_avatar()

### 键盘鼠标 支持的动作:
key_press(key)

### 其他 支持的动作:
'''
from player.play_program import play_program
from player.avatar_player import play_avatar, show_text, stop_avatar
from player.slide_player import get_status as get_slide_player_status, play_slide, next_page, prev_page
from player.video_player import get_status as get_video_player_status, play_video, forward_video, backward_video, stop_video
from player.web_player import get_status as get_web_player_status, open_url
from player.key_mouse import key_press
