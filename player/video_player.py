'''
播放器采用 VLC + RC(TCP) 控制的方案实现。
功能包括：
  - 应用程序状态检测功能（是否运行，RC端口是否可达）

+----[ 远程控制命令 ]
|
| add XYZ  . . . . . . . . . . . . 将 XYZ 添加到播放列表
| enqueue XYZ  . . . . . . . . . 将 XYZ 加入播放列表队列
| playlist . . . . .  显示当前播放列表中的项目
| play . . . . . . . . . . . . . . . . . . 播放流
| stop . . . . . . . . . . . . . . . . . . 停止流
| next . . . . . . . . . . . . . .  下一个播放列表项目
| prev . . . . . . . . . . . .  上一个播放列表项目
| goto . . . . . . . . . . . . . .  转到索引号对应的项目
| repeat [on|off] . . . .  切换播放列表项目循环
| loop [on|off] . . . . . . . . . 切换播放列表循环
| random [on|off] . . . . . . .  切换随机跳转
| clear . . . . . . . . . . . . . . 清除播放列表
| status . . . . . . . . . . . 当前播放列表状态
| title [X]  . . . . . . 设置/获取当前项目标题
| title_n  . . . . . . . .  当前项目的下一个标题
| title_p  . . . . . .  当前项目的上一个标题
| chapter [X]  . . . . 设置/获取当前项目的章节
| chapter_n  . . . . . .  当前项目的下一个章节
| chapter_p  . . . .  当前项目的上一个章节
|
| seek X . . . 定位，单位为秒, 例如 `seek 12'
| pause  . . . . . . . . . . . . . . . .  切换暂停
| fastforward  . . . . . . . .  .  速度最快
| rewind  . . . . . . . . . . . .  速度最慢
| faster . . . . . . . . . .  快速播放流
| slower . . . . . . . . . .  慢速播放流
| normal . . . . . . . . . .  常速播放流
| frame. . . . . . . . . .  逐帧播放
| f [on|off] . . . . . . . . . . . . 切换全屏
| info . . . . .  当前流的信息
| stats  . . . . . . . .  显示统计信息
| get_time . . 从流开始时经过的秒数
| is_playing . . . .  如果流在播放为 1, 否则为 0
| get_title . . . . .  当前流的标题
| get_length . . . .  当前流的长度
|
| volume [X] . . . . . . . . . .  设置/获取音频音量
| volup [X]  . . . . . . .  提升音频音量 X 级
| voldown [X]  . . . . . .  降低音频音量 X 级
| adev [设备]    . . . . . . . .  设置/获取音频设备
| achan [X]. . . . . . . . . .  设置/获取声道
| atrack [X] . . . . . . . . . . . 设置/获取音轨
| vtrack [X] . . . . . . . . . . . 设置/获取视频轨道
| vratio [X]  . . . . . . . 设置/获取视频宽高比
| vcrop [X]  . . . . . . . . . . .  设置/获取视频裁剪
| vzoom [X]  . . . . . . . . . . .  设置/获取视频缩放
| snapshot . . . . . . . . . . . . 获取视频截图
| strack [X] . . . . . . . . .  设置/获取字幕轨道
| key [热键名] . . . . . .  模拟按下热键
|
| help . . . . . . . . . . . . . . . 此帮助信息
| logout . . . . . . .  退出 (套接字连接模式下)
| quit . . . . . . . . . . . . . . . . . . .  退出 vlc
|
+----[ 帮助结束 ]

''' 

import os
import socket
import subprocess
import time
import yaml
from dataclasses import dataclass


@dataclass
class VLCConfig:
    vlc_exe: str = "vlc.exe"
    host: str = "127.0.0.1"
    port: int = 9999
    fullscreen: bool = True
    loop: bool = False
    no_title: bool = True

@dataclass
class VLCStatus:
    is_running: bool = False
    is_playing: bool = False
    state: str = None                 # playing / paused / stopped / unknown
    media: str = None          # 当前播放的文件或URL
    position_sec: int = -1   # 当前播放时间（秒）
    duration_sec: int = -1   # 总时长（秒）
    progress: float = 0.0     # 0.0 ~ 1.0

class VLCRemote:
    """
    方案D：独立启动 VLC.exe + 通过 RC(TCP) 控制
    Python 退出后 VLC 仍继续运行（因为是独立进程）
    """

    def __init__(self) -> None:
        self.cfg = VLCConfig()
        # 读取配置文件
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
            self.cfg.vlc_exe = cfg.get('player', {}).get('videoplayer', {}).get('exe', 'vlc.exe')
            self.cfg.host = cfg.get('player', {}).get('videoplayer', {}).get('host', '127.0.0.1')
            self.cfg.port = cfg.get('player', {}).get('videoplayer', {}).get('port', 9999)

        if not os.path.exists(self.cfg.vlc_exe):
            raise FileNotFoundError(f"vlc.exe not found: {self.cfg.vlc_exe}")
        self._proc: subprocess.Popen | None = None

    # ---------- 基础：发送 RC 命令 ----------
    def _send_rc(self, command: str, timeout: float = 0.8, wait_return: bool = False) -> None:
        """
        向 VLC RC 端口发送命令。VLC 没启动/端口没开会抛异常。
        Socket 保存为内部变量,读取操作可获得返回结果。
        """
        # with socket.create_connection((self.cfg.host, self.cfg.port), timeout=timeout) as s:
        #     ret = s.sendall((command.strip() + "\n").encode("utf-8"))
        try:
            with socket.create_connection((self.cfg.host, self.cfg.port), timeout=timeout) as s:
                s.sendall((command.strip() + "\n").encode("utf-8"))
                if wait_return:
                    time.sleep(0.1)
                    data = s.recv(8192)
                    return data.decode("utf-8", errors="ignore")
        except socket.error as e:
            raise OSError(f"Failed to send RC command to VLC: {e}") from e

    # 获取vlc的当前状态以及正在播放的内容和进度
    def get_status(self) -> VLCStatus:
        # 初始化
        status = VLCStatus()
        # 读取运行状态
        status.is_running = self.is_running()
        if not status.is_running:
            return status
        # 读取播放状态
        response = self._send_rc("is_playing", wait_return=True)
        status.is_playing = True if int(response.strip())==1 else False
        # 读取当前位置
        status.position_sec = int(self._send_rc("get_time", wait_return=True).strip())
        # 读取总长度
        status.duration_sec = int(self._send_rc("get_length", wait_return=True).strip())
        # 读取进度
        if status.duration_sec > 0:
            status.progress = int(10000 * status.position_sec / status.duration_sec)/100
        else:
            status.progress = 0.0
        # 读取标题
        status.media = self._send_rc("get_title", wait_return=True).strip()
        # 获取状态
        response = self._send_rc("status", wait_return=True)
        for line in response.splitlines():
            print(line)
            # key, value = line.split(": ", maxsplit=1)
            # status[key] = value
        return status

    def get_playlist(self) -> str | None:
        """
        从 playlist 输出中提取当前播放的媒体路径/URL
        """
        response = self._send_rc("playlist", wait_return=True)
        print(response)
        # 示例： |  *0 - file:///D:/videos/demo.mp4
        for line in response.splitlines():
            if "*" in line:
                return line.split("-", 1)[-1].strip()
        return None

    def is_running(self) -> bool:
        try:
            response = self._send_rc("help", timeout=0.2, wait_return=True)
            # print(response)
            return True
        except OSError:
            return False

    # ---------- 启动 VLC（独立进程） ----------
    def start_vlc(self, media_path: str | None = None) -> None:
        """
        启动 VLC.exe 并开启 RC 接口。
        如果 media_path 不为空，则启动后直接播放该媒体。
        """
        if not os.path.isfile(self.cfg.vlc_exe):
            raise FileNotFoundError(f"vlc.exe not found: {self.cfg.vlc_exe}")

        cmd = [
            self.cfg.vlc_exe,
            "--intf", "dummy",                 # 无需VLC主UI交互也能播放（更像播放器服务）
            "--extraintf", "rc",
            "--rc-host", f"{self.cfg.host}:{self.cfg.port}",
            "--rc-quiet",                      # 减少输出
        ]

        if self.cfg.fullscreen:
            cmd.append("--fullscreen")
        if self.cfg.loop:
            cmd.append("--loop")
        if self.cfg.no_title:
            cmd.append("--no-video-title-show")

        # 如果指定媒体文件/URL，就让 VLC 直接播放它
        if media_path:
            cmd.append(media_path)

        # 独立进程启动：Python 不等待
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )

        # 等待 RC 端口就绪（最多 2 秒）
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if self.is_running():
                return
            time.sleep(0.05)

        # 如果没起来，多半是端口被占用或 VLC 没启动成功
        raise RuntimeError("VLC started but RC interface not reachable. Check port/permissions.")

    # ---------- 你要的 5 个控制接口 ----------
    def play_video(self, media_path: str) -> None:
        """
        如果 VLC 没启动：启动并播放
        如果 VLC 已启动：追加并播放该媒体（用 add）
        """
        if not self.is_running():
            self.start_vlc(media_path)
            return

        # 已在运行：用 add 播放新的媒体
        self._send_rc(f'add "{media_path}"')

    def pause_video(self) -> None:
        self._send_rc("pause")

    def stop_video(self) -> None:
        self._send_rc("stop")

    def forward_video(self, seconds: int = 10) -> None:
        self._send_rc(f"seek +{seconds}")

    def backward_video(self, seconds: int = 10) -> None:
        self._send_rc(f"seek -{seconds}")

    # ---------- 可选：让 VLC 退出 ----------
    def quit_vlc(self) -> None:
        """
        关闭 VLC（可选）。
        """
        self._send_rc("quit")


def play_video(url):
    controller = VLCRemote()
    controller.play_video(url)

def stop_video():
    controller = VLCRemote()
    controller.stop_video()