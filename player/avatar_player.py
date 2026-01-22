'''
avatar_player 实现数字人的播放功能

数字人播放器启动后,开启ws://localhost:59059端口,等待客户端连接;

接收到客户端发送的数据后,根据数据内容进行相应的操作;

主要 动作 包括：

### 1. 播放列表

新的播放列表下发后;冲掉之前的播放列表,并立即以新的播放列表播放;下发的playlist列表为空时,清除播放列表(起到停止的作用);
逻辑：用新的播放列表替换以前的列表。

```JSON
{"tasks": "playlist",
  "playlist": [
      {"video": "../assets/videos/video1.webm", "loop": 1, "left": 1200, "top": 700, "width": 100, "height": 300}, //播放1次
       {"image": "../assets/videos/video2.jpeg", "loop": 3}, //持续3秒
       {"video": "../assets/videos/video1.webm", "loop": -1}  //无限循环
        ...
    ]
}
```

### 2. 在数字人的文本显示区中显示信息

```JSON
{"tasks": "text",
  "text": "这里是文本信息，可以显示在数字人身上。",
  "duration": 1
  }
```

### 3. 播放/暂停

保持播放列表，当前播放内容暂停

```JSON
{"tasks": "play/pause"}
```

### 4. 停止

在当前的播放列表, 继续当前播放内容

```JSON
{"tasks": "stop"}
```

创建一个 AvatarController 类

class AvatarController:
    def __init__(self):
        pass
```

'''

def play_avatar(playlist:list[dict[str, str | list[str]]]) -> None:
    pass

def show_text(text: str, duration: int = 1) -> None:
    pass

def pause_avatar() -> None:
    pass

def stop_avatar() -> None:
    pass