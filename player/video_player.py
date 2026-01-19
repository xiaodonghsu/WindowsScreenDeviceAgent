# import subprocess

# def play_video(url):
#     subprocess.Popen([
#         "chrome",
#         "--start-fullscreen",
#         url
#     ])

# def stop_video(url):
#     subprocess.Popen([
#         "chrome",
#         "--start-fullscreen",
#         url
#     ])

# import vlc
# import yaml
# import time
# import os


# class VLCController:
#     def __init__(self):
#         """
#         vlc_path: VLC 安装路径（可选）
#         """
#         # 加载 config.yaml 中的 videoplayer 路径
#         with open("config.yaml", "r") as f:
#             cfg = yaml.safe_load(f)
#         vlc_path = cfg.get("player", {}).get("videoplayer", {}).get("exe", "")
#         if vlc_path == "":
#             self.instance = vlc.Instance()
#         else:
#             self.instance = vlc.Instance(vlc_path)
#         self.player = self.instance.media_player_new()

#     def play_video(self, video_path: str):
#         media = self.instance.media_new(video_path)
#         self.player.set_media(media)
#         self.player.play()

#     def pause_video(self):
#         self.player.pause()

#     def stop_video(self):
#         self.player.stop()

#     def forward_video(self, seconds: int = 10):
#         """
#         快进，默认 10 秒
#         """
#         current_time = self.player.get_time()  # 毫秒
#         if current_time != -1:
#             self.player.set_time(current_time + seconds * 1000)

#     def backward_video(self, seconds: int = 10):
#         """
#         后退，默认 10 秒
#         """
#         current_time = self.player.get_time()
#         if current_time != -1:
#             new_time = max(0, current_time - seconds * 1000)
#             self.player.set_time(new_time)


import os
import socket
import subprocess
import time
import yaml
from dataclasses import dataclass


@dataclass
class VLCConfig:
    vlc_exe: str = ""
    host: str = "127.0.0.1"
    port: int = 9999
    fullscreen: bool = True
    loop: bool = False
    no_title: bool = True


class VLCRemote:
    """
    方案D：独立启动 VLC.exe + 通过 RC(TCP) 控制
    Python 退出后 VLC 仍继续运行（因为是独立进程）
    """

    def __init__(self, config: VLCConfig):
        self.cfg = config
        self._proc: subprocess.Popen | None = None

    # ---------- 基础：发送 RC 命令 ----------
    def _send_rc(self, command: str, timeout: float = 0.8) -> None:
        """
        向 VLC RC 端口发送命令。VLC 没启动/端口没开会抛异常。
        """
        with socket.create_connection((self.cfg.host, self.cfg.port), timeout=timeout) as s:
            s.sendall((command.strip() + "\n").encode("utf-8"))

    def is_rc_alive(self) -> bool:
        try:
            self._send_rc("help", timeout=0.2)
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
            if self.is_rc_alive():
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
        if not self.is_rc_alive():
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


if __name__ == "__main__":
    # 读取配置
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    vlc_exe = cfg.get("player", {}).get("videoplayer", {}).get("exe", "vlc.exe")
    print(vlc_exe)
    cfg = VLCConfig(
        vlc_exe=vlc_exe,
        host="127.0.0.1",
        port=9999,
        fullscreen=True,
        loop=False
    )

    vlc = VLCRemote(cfg)

    video = 'D:\\Files\\Downloads\\xunjian.mp4'
    print(f"Playing video: {video}")
    vlc.play_video(video)

    time.sleep(3)
    print("Forwarding for 10 seconds...")
    vlc.forward_video()      # +10s
    time.sleep(2)
    print("Pausing for 2 seconds...")
    vlc.pause_video()
    time.sleep(2)
    
    print("Pausing for 2 seconds...")
    vlc.pause_video()        # 再次 pause = 恢复播放
    time.sleep(2)
    
    print("Backwarding for 5 seconds...")
    vlc.backward_video(5)    # -5s
    time.sleep(2)
    
    print("Stopping...")
    vlc.stop_video()

    # Python 结束后，VLC 仍可保持运行（除非你调用 quit_vlc）
    # vlc.quit_vlc()
