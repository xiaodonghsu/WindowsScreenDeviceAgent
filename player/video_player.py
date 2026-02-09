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

import re
from typing import Any


import os
import socket
import subprocess
import psutil
import time
from dataclasses import dataclass, asdict

import logging
from common.config import get_device_name
logger = logging.getLogger(get_device_name())

@dataclass
class VideoPlayerConfig:
    exe: str = "vlc.exe"
    host: str = "127.0.0.1"
    port: int = 9999
    fullscreen: bool = True
    loop: bool = False
    no_title: bool = True

@dataclass
class VideoPlayerStatus:
    is_running: bool = False
    is_playing: bool = False
    state: str = ""                 # playing / paused / stopped / unknown
    media: str = ""          # 当前播放的文件或URL
    position_sec: int = -1   # 当前播放时间（秒）
    duration_sec: int = -1   # 总时长（秒）
    progress: float = 0.0     # 0.0 ~ 1.0

class VideoPlayerRemote:
    """
    方案D：独立启动 VideoPlayer.exe + 通过 RC(TCP) 控制
    Python 退出后 VideoPlayer 仍继续运行（因为是独立进程）
    """

    def __init__(self) -> None:
        self.config = VideoPlayerConfig()
        self._proc: subprocess.Popen | None = None

    # ---------- 基础：发送 RC 命令 ----------
    def _send_rc(self, command: str, timeout: float = 0.8, wait_return_time: float = 0.1):
        """
        向 VideoPlayer RC 端口发送命令。VideoPlayer 没启动/端口没开会抛异常。
        Socket 保存为内部变量,读取操作可获得返回结果。
        """
        # with socket.create_connection((self.config.host, self.config.port), timeout=timeout) as s:
        #     ret = s.sendall((command.strip() + "\n").encode("utf-8"))
        try:
            with socket.create_connection((self.config.host, self.config.port), timeout=timeout) as s:
                s.sendall((command.strip() + "\n").encode("utf-8"))
                if wait_return_time > 0:
                    time.sleep(wait_return_time)
                    data = s.recv(8192)
                    return data.decode("utf-8", errors="ignore")
        except socket.error as e:
            logger.error(f"Failed to send RC command to VideoPlayer: {e}")
            return None

    def _send_rc_list(self, command_list: list[str], timeout: float = 0.8, wait_return_time: float = 0.1) -> list[str|None] | None:
        """
        向 VideoPlayer RC 端口发送命令。VideoPlayer 没启动/端口没开会抛异常。
        Socket 保存为内部变量,读取操作可获得返回结果。
        """
        # with socket.create_connection((self.config.host, self.config.port), timeout=timeout) as s:
        #     ret = s.sendall((command.strip() + "\n").encode("utf-8"))
        response = []
        try:
            s = socket.create_connection((self.config.host, self.config.port), timeout=timeout)
        except socket.error as e:
            return None
        for command in command_list:
            try:
                s.sendall((command.strip() + "\n").encode("utf-8"))
                if wait_return_time > 0:
                    time.sleep(wait_return_time)
                    data = s.recv(8192)
                    response.append( data.decode("utf-8", errors="ignore"))
            except socket.error as e:
                logger.error(f"Failed to send RC command to VideoPlayer: {e}")
                response.append( None)
        return response

    def send_command(self, command: str, timeout: float = 0.8, wait_return_time: float = 0.1):
        response = self._send_rc(command, timeout, wait_return_time)
        return response

    # 获取vlc的当前状态以及正在播放的内容和进度
    def get_status(self) -> VideoPlayerStatus:
        # 初始化
        status = VideoPlayerStatus()
        # 读取运行状态
        status.is_running = self.is_running()
        if not status.is_running:
            return status
        # 读取播放状态
        response = self._send_rc("is_playing").strip()
        status.is_playing = True if int(response)==1 else False
        # 读取当前位置
        response = self._send_rc("get_time").strip()
        try:
            status.position_sec = int(response)
        except ValueError:
            pass
        # 读取总长度
        response = self._send_rc("get_length").strip()
        try:
            status.duration_sec = int(response)
        except ValueError:
            pass
        # 读取进度
        if status.duration_sec > 0:
            status.progress = int(10000 * status.position_sec / status.duration_sec)/100
        else:
            status.progress = 0.0
        # 读取标题
        status.media = self._send_rc("get_title").strip()
        # 获取状态
        response = self._send_rc("status")
        '''
        status 命令返回值:
        ## 典型播放状态
        status change: ( new input: file:///D:/Files/Downloads/xunjian.mp4 )
        status change: ( audio volume: 269 )
        status change: ( play state: 3 )
        status: returned 0 (no error)

        ## 典型暂停状态(暂停后第一次查询)
        status change: ( pause state: 4 )
        输入“pause”可继续。
        status: returned 0 (no error)

        ## (暂停后再次查询)
        输入“pause”可继续。
        status: returned 0 (no error)

        ## 停止状态
        status change: ( audio volume: 269 )
        status change: ( stop state: 5 )
        status: returned 0 (no error)


        '''
        for line in response.splitlines():
            logger.debug(line)
            m = re.compile(pattern = r'\((.*?)\)').search(line)
            if m:
                if ":" in m.group(1):
                    key, value = m.group(1).split(": ", maxsplit=1)
                    if key.endswith("state"):
                        status.state = key.strip().split(" ")[0]
                        break
            else:
                if "pause" in line:
                    status.state = "pause"
                    break
            # key, value = line.split(": ", maxsplit=1)
            # status[key] = value
        return status

# 获取vlc的当前状态以及正在播放的内容和进度
    def get_status_list(self) -> VideoPlayerStatus:
        # 初始化
        status = VideoPlayerStatus()
        # 读取运行状态
        status.is_running = self.is_running()
        if not status.is_running:
            return status
        command_list = ["is_playing", "get_time", "get_length", "get_title", "status"]
        response = self._send_rc_list(command_list)
        if response is None:
            return status
        # 读取播放状态
        try:
            status.is_playing =  True if int(response[0].strip().splitlines()[0].strip())==1 else False
        except:
            pass
        # 读取当前位置
        try:
            status.position_sec = int(response[1].strip().splitlines()[0].strip())
        except ValueError:
            pass
        # 读取总长度
        try:
            status.duration_sec = int(response[2].strip().splitlines()[0].strip())
        except ValueError:
            pass
        # 计算进度
        if status.duration_sec > 0:
            status.progress = int(10000 * status.position_sec / status.duration_sec)/100
        else:
            status.progress = 0.0
        # 读取标题
        try:
            status.media = response[3].strip().splitlines()[0].strip()
        except:
            pass
        # 获取状态
        '''
        status 命令返回值:
        ## 典型播放状态
        status change: ( new input: file:///D:/Files/Downloads/xunjian.mp4 )
        status change: ( audio volume: 269 )
        status change: ( play state: 3 )
        status: returned 0 (no error)

        ## 典型暂停状态(暂停后第一次查询)
        status change: ( pause state: 4 )
        输入“pause”可继续。
        status: returned 0 (no error)

        ## (暂停后再次查询)
        输入“pause”可继续。
        status: returned 0 (no error)

        ## 停止状态
        status change: ( audio volume: 269 )
        status change: ( stop state: 5 )
        status: returned 0 (no error)


        '''
        for line in response[4].strip().splitlines():
            logger.debug(msg=line)
            m = re.compile(pattern = r'\((.*?)\)').search(line)
            if m:
                if ":" in m.group(1):
                    key, value = m.group(1).split(": ", maxsplit=1)
                    if key.endswith("state"):
                        status.state = key.strip().split(" ")[0]
                        break
            else:
                if "pause" in line:
                    status.state = "pause"
                    break
            # key, value = line.split(": ", maxsplit=1)
            # status[key] = value
        return status


    def get_playlist(self) -> str | None:
        """
        从 playlist 输出中提取当前播放的媒体路径/URL
        """
        response = self._send_rc("playlist")
        logger.debug(response)
        # 示例： |  *0 - file:///D:/videos/demo.mp4
        for line in response.splitlines():
            if "*" in line:
                return line.split("-", 1)[-1].strip()
        return None

    def is_running(self) -> bool:
        if len(self.get_processes_by_name(self.config.exe)) == 0:
            return False
        if self._send_rc("help") is None:
            return False
        return True

    def get_processes_by_name(self, exe_name=None) -> list[int]:
        """
        获取正在运行的 VideoPlayer 进程的 PID
        """
        if exe_name is None:
            exe_name = self.config.exe
        player_exe_basename = os.path.basename(exe_name)
        processes = []
        for proc in psutil.process_iter():
            if proc.name() == player_exe_basename:
                processes.append(proc.pid)
        return processes

    def kill_processes_by_name(self, exe_name=None) -> None:
        """
        杀死所有正在运行的 VideoPlayer 进程
        """
        if exe_name is None:
            exe_name = self.config.exe
        player_exe_basename = os.path.basename(exe_name)
        for proc in psutil.process_iter():
            if proc.name() == player_exe_basename:
                try:
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

    # ---------- 启动 VideoPlayer（独立进程） ----------
    def start_vlc(self, timeout: int = 5) -> bool:
        """
        启动 VideoPlayer.exe 并开启 RC 接口。
        如果 media_path 不为空，则启动后直接播放该媒体。
        """
        # 读取配置文件
        if not os.path.exists(self.config.exe):
            from system.config import get_app_path
            app_path = get_app_path(self.config.exe)
            if os.path.exists(app_path):
                self.config.exe = app_path
            else:
                logger.error(f"{self.config.exe} not found")
                raise FileNotFoundError(f"{self.config.exe} not found")


        # 检查是程序是否运行
        if self.is_running():
            logger.info("VideoPlayer is already running")
        else:
            logger.info("Try to start VideoPlayer")
            _ = self.kill_processes_by_name(exe_name=self.config.exe)
            cmd = [
                self.config.exe,
                "--intf", "dummy",                 # 无需VideoPlayer主UI交互也能播放（更像播放器服务）
                "--extraintf", "rc",
                "--rc-host", f"{self.config.host}:{self.config.port}",
                "--rc-quiet",                      # 减少输出
            ]

            if self.config.fullscreen:
                cmd.append("--fullscreen")
            if self.config.loop:
                cmd.append("--loop")
            if self.config.no_title:
                cmd.append("--no-video-title-show")

            # 独立进程启动：Python 不等待
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True
            )

            # 等待 RC 端口就绪（最多 timeout 秒）
            t0 = time.time()
            while time.time()-t0 < timeout:
                if self.is_running():
                    logger.info(f"{self.config.exe} started and RC reached at {int((time.time()-t0)*1000)/1000} s.")
                    return False
                time.sleep(0.05)

            # 如果没起来，多半是端口被占用或 VideoPlayer 没启动成功
            logger.error("VideoPlayer started but RC interface not reachable. Check port/permissions.")
            return False
        return True

    # ---------- 5 个控制接口 ----------
    def play_video(self, media_path: str) -> None:
        """
        如果 VideoPlayer 没启动：启动并播放
        如果 VideoPlayer 已启动：追加并播放该媒体（用 add）
        """
        if not media_path.startswith("http"):
            if not os.path.exists(media_path):
                logger.error(f"media file: {media_path} not exists!")
                return
        retry = 2
        while retry >=0:
            if not self.is_running():
                self.start_vlc()
            else:
                break
            retry -= 1
        # 已在运行：用 add 播放新的媒体
        if self.is_running():
            response = self._send_rc("clear")
            logger.debug(f"clear command returned: {response}")
            response = self._send_rc(f'add "{media_path}"')
            logger.debug(f"add command returned: {response}")

    def pause_video(self) -> None:
        # 读取播放状态
        response = self._send_rc("is_playing")
        try:
            response_code = int(response.strip())
        except Exception as e:
            response_code = 0
            logger.warning(f"Unexpect response {response}. error: {e}")
        is_playing = True if response_code == 1 else False
        if is_playing:
            logger.debug(f"video is playing, send pause command")
            response = self._send_rc("pause")
            logger.debug(f"Pause command returned: {response}")

    def stop_video(self) -> None:
        self._send_rc("stop")

    def forward_video(self, seconds: int = 10) -> None:
        self._send_rc(f"seek +{seconds}")

    def backward_video(self, seconds: int = 10) -> None:
        self._send_rc(f"seek -{seconds}")

    # ---------- 可选：让 VideoPlayer 退出 ----------
    def quit_vlc(self) -> None:
        """
        关闭 VideoPlayer（可选）。
        """
        self._send_rc("quit")

def get_status():
    """
    获取播放器状态
    """
    controller = VideoPlayerRemote()
    return asdict(controller.get_status_list())

def play_video(url, start_pause=False):
    controller = VideoPlayerRemote()
    controller.play_video(url)
    if start_pause:
        controller.pause_video()

def stop_video():
    controller = VideoPlayerRemote()
    controller.stop_video()

def forward_video(seconds: int = 10):
    controller = VideoPlayerRemote()
    controller.forward_video(seconds)

def backward_video(seconds: int = 10):
    controller = VideoPlayerRemote()    
    controller.backward_video(seconds)