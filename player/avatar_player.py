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

import asyncio
import json
import threading
from typing import Any

if True:
    try:
        import websockets
        websockets_available = True
    except ImportError:
        websockets = None
        websockets_available = False

from common.logger import setup_logger

logger = setup_logger("avatar-player")


class AvatarController:
    """数字人播放器控制类"""

    def __init__(self, host: str = "localhost", port: int = 59059) -> None:
        self.host: str = host
        self.port: int = port
        self.server: Any = None
        self.playlist: list[dict[str, Any]] = []
        self.current_index: int = 0
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.loop: threading.Thread = threading.Thread(target=self._run_server, daemon=True)
        self.loop.start()

    def _run_server(self) -> None:
        """运行 WebSocket 服务器"""
        async def handle_client(websocket: Any, path: str) -> None:
            try:
                async for message in websocket:
                    logger.info(f"Received message: {message}")
                    try:
                        data = json.loads(message)
                        self._handle_command(data)
                        await websocket.send(json.dumps({"status": "success"}))
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")
                        await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
                    except Exception as e:
                        logger.error(f"Error handling command: {e}")
                        await websocket.send(json.dumps({"status": "error", "message": str(e)}))
            except Exception as e:
                logger.info("Client disconnected or error: {e}")

        async def start_server() -> None:
            if not websockets_available:
                logger.error("websockets module not available")
                return
            if websockets is not None:
                self.server = await websockets.serve(handle_client, self.host, self.port)
                logger.info(f"Avatar player server started on ws://{self.host}:{self.port}")
                await self.server.wait_closed()

        asyncio.run(start_server())

    def _handle_command(self, data: dict[str, Any]) -> None:
        """处理客户端命令"""
        tasks = data.get("tasks")

        if tasks == "playlist":
            self._handle_playlist(data.get("playlist", []))
        elif tasks == "text":
            self._handle_text(data.get("text", ""), data.get("duration", 1))
        elif tasks == "play/pause":
            self._handle_play_pause()
        elif tasks == "stop":
            self._handle_stop()
        else:
            logger.warning(f"Unknown task: {tasks}")

    def _handle_playlist(self, playlist: list[dict[str, Any]]) -> None:
        """处理播放列表"""
        if not playlist:
            self.playlist = []
            self.current_index = 0
            self.is_playing = False
            logger.info("Playlist cleared")
        else:
            self.playlist = playlist
            self.current_index = 0
            self.is_playing = True
            self.is_paused = False
            logger.info(f"New playlist loaded with {len(playlist)} items")
            self._play_current()

    def _handle_text(self, text: str, duration: int) -> None:
        """处理文本显示"""
        logger.info(f"Display text: '{text}' for {duration} seconds")
        # TODO: 实现在数字人身上显示文本的逻辑

    def _handle_play_pause(self) -> None:
        """处理播放/暂停"""
        if self.is_paused:
            self.is_paused = False
            logger.info("Resumed playing")
            self._play_current()
        else:
            self.is_paused = True
            logger.info("Paused playing")

    def _handle_stop(self) -> None:
        """处理停止"""
        self.is_playing = False
        self.is_paused = False
        self.current_index = 0
        logger.info("Stopped playing")

    def _play_current(self) -> None:
        """播放当前项目"""
        if not self.playlist or self.current_index >= len(self.playlist):
            self.is_playing = False
            logger.info("Playlist finished or empty")
            return

        item = self.playlist[self.current_index]
        logger.info(f"Playing item {self.current_index}: {item}")

        # 根据类型播放不同的媒体
        if "video" in item:
            self._play_video(item)
        elif "image" in item:
            self._play_image(item)

    def _play_video(self, item: dict[str, Any]) -> None:
        """播放视频"""
        video_path = item.get("video")
        loop = item.get("loop", 1)
        logger.info(f"Playing video: {video_path}, loop: {loop}")
        # TODO: 调用视频播放器播放视频

    def _play_image(self, item: dict[str, Any]) -> None:
        """播放图片"""
        image_path = item.get("image")
        duration = item.get("loop", 1)
        logger.info(f"Displaying image: {image_path}, duration: {duration}s")
        # TODO: 调用图片播放器显示图片

    def next(self) -> None:
        """下一个项目"""
        self.current_index += 1
        if self.current_index >= len(self.playlist):
            self.current_index = 0
            # 检查是否需要循环播放
            if self.playlist and self.playlist[0].get("loop", 1) == -1:
                logger.info("Looping playlist")
            else:
                self.is_playing = False
                logger.info("End of playlist")
                return
        self._play_current()

    def get_status(self) -> dict[str, Any]:
        """获取当前状态"""
        return {
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "current_index": self.current_index,
            "playlist_size": len(self.playlist),
            "current_item": self.playlist[self.current_index] if self.playlist and self.current_index < len(self.playlist) else None
        }


# 全局控制器实例
_controller: AvatarController | None = None
_lock = threading.Lock()


def get_controller() -> AvatarController:
    """获取或创建控制器实例"""
    global _controller
    if _controller is None:
        with _lock:
            if _controller is None:
                _controller = AvatarController()
    return _controller


def play_avatar(playlist: list[dict[str, str | list[str]]]) -> None:
    """播放数字人播放列表"""
    controller = get_controller()
    playlist_typed = [item for item in playlist]
    controller._handle_playlist(playlist_typed)


def show_text(text: str, duration: int = 1) -> None:
    """在数字人文本显示区显示信息"""
    controller = get_controller()
    controller._handle_text(text, duration)


def pause_avatar() -> None:
    """暂停/恢复播放"""
    controller = get_controller()
    controller._handle_play_pause()


def stop_avatar() -> None:
    """停止播放"""
    controller: AvatarController = get_controller()
    controller._handle_stop()