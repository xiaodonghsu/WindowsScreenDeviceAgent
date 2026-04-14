from dataclasses import dataclass, asdict
import os
import subprocess
import psutil
import shutil
import requests
import websocket
import json
import time
import logging
from common.config import get_device_name
logger = logging.getLogger(get_device_name())

@dataclass
class WebPlayerStatus:
    is_running: bool = False
    browser: str = ""
    tabs_count: int = 0
    tab_tile: str = ""
    tab_url: str = ""
    tab_type: str = ""

@dataclass
class WebPlayerConfig:
    exe: str = "chrome.exe"
    # "--remote-debugging-port=9222",
    debug_port = 9222
    # "--user-data-dir=%TEMP%\\ChromeDevSession",
    user_data_dir = "%TEMP%\\ChromeDevSession"
    exe_args = [
        "--start-fullscreen",
        "--remote-allow-origins=*",
        "--UseBasicParsing",
        "--disable-session-crashed-bubble",
        "--disable-infobars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-restore-session-state",
        "--disable-notifications",
        "--language=zh-CN",
        "--disable-features=Translate,TranslateUI",
        "--autoplay-policy=no-user-gesture-required"
      ]

class WebPlayer:
    def __init__(self):
        self.config = WebPlayerConfig()
        os_temp_dir = os.environ.get("TEMP")
        if "%TEMP%" in self.config.user_data_dir:
            self.config.user_data_dir = self.config.user_data_dir.replace("%TEMP%", os_temp_dir)
        self.message_id: int = 0
        self.browser_info = None

    def _start_browser(self, url:str="about:blank") -> bool:
        '''
        检查浏览器是否已经打开,如果没有打开,则打开浏览器
        检查标签页的数量，从后到前关闭标签页；是否有指定的url,如果没有,则打开url
        '''
        # 直接读取9222端口来测试
        tabs = self.get_tabs()
        if tabs is None:
            # 检查同类型的浏览器已经打开,如果有必须关闭
            logger.info("无可控的浏览器打开,尝试关闭可能已经打开的浏览器")
            self._terminate_browser()
            # 启动浏览器
            # 清除浏览器的用户数据目录
            # self._clear_browser_user_data_dir()
            logger.info("尝试启动可控的浏览器")
            self._browser_startup(url)
            logger.info("确认浏览器是否准备好")
            tabs = self.get_tabs()
            if tabs is None:
                logger.error("浏览器启动失败!")
                return False
            logger.info("浏览器启动成功")
            return True
        else:
            if len(tabs) > 1:
                logger.info(f"浏览器标签页数量: {len(tabs)}")
                # 超过1个tab时, 关闭其他所有的tab
                for i in range(len(tabs)-1, 0, -1):
                    logger.info(f"关闭标签页: {tabs[i].get("title", "")}")
                    self.close_tab(tabs[i].get("id", ""))
            logger.info(f"打开 {url}")
            self.browser_interactive(url)
        return True

    def _clear_browser_user_data_dir(self):
        if os.path.exists(self.config.user_data_dir):
            # windows下清除目录
            try:
                logger.info(f"删除浏览器用户数据目录: {self.config.user_data_dir}")
                shutil.rmtree(self.config.user_data_dir)
            except Exception as e:
                logger.warning(f"删除浏览器用户数据目录失败: {e}")
        logger.info(f"清除浏览器用户数据目录完成: {self.config.user_data_dir}")

    def get_status(self):
        status: WebPlayerStatus = WebPlayerStatus()
        browser_info = self.get_info()
        if browser_info is None:
            status.is_running = False
            return status
        status.is_running = True
        status.browser = browser_info.get("Browser")
        tabs = self.get_tabs()
        status.tabs_count = len(tabs)
        if status.tabs_count > 0:
            status.tab_tile = tabs[0].get("title")
            status.tab_url = tabs[0].get("url")   
            status.tab_type = tabs[0].get("type")
        return status

    def _browser_startup(self, url="about:blank"):
        # 获取可执行文件的全路径
        if not os.path.exists(self.config.exe):
            from system.config import get_app_path
            app_path = get_app_path(self.config.exe)
            if os.path.exists(app_path):
                self.config.exe = app_path
            else:
                logger.error(f"{self.config.exe} not found")
                raise ValueError(f"{self.config.exe} not found")
        # 组织命令行
        cmdline = [f'{self.config.exe}',]
        # 调试基本参数
        cmdline.append(f"--remote-debugging-port={self.config.debug_port}")
        # 环境参数
        cmdline.append (f"--user-data-dir={self.config.user_data_dir}") 
        # 其他参数表
        for arg in self.config.exe_args:
            cmdline.append(arg)
        cmdline.append(url)
        logger.info(f"启动浏览器: {' '.join(cmdline)}")
        subprocess.Popen(cmdline)
        logger.info(f"等待浏览器启动完成")
        time.sleep(2)

    def _terminate_browser(self):
        browser_name = os.path.basename(self.config.exe).lower()
        try:
            for process in psutil.process_iter():
                if process.name().lower() == browser_name:
                    logger.info(f"终止进程: {process.pid} - {process.nameline()}")
                    process.terminate()
                    time.sleep(1)
        except:
            pass

    def get_tabs(self):
        result = []
        try:
            response = requests.get(f'http://localhost:{self.config.debug_port}/json', timeout=0.5)
            tabs = response.json()
            # 清除掉url是 chrome: 起头的,从列表中清除
            for tab in tabs:
                if tab.get("type") == "page":
                    result.append(tab)
            return result
        except Exception as e:
            return None

    def close_tab(self, tab_id: str) -> None:
        try:
            response = requests.get(f'http://localhost:{self.config.debug_port}/json/close/{tab_id}', timeout=0.2)
            time.sleep(1)
        except Exception as e:
            logger.error(f"关闭浏览器标签页{tab_id}失败: {e}") 

    def close_browser(self) -> None:
        if self.get_info() is None:
            return True
        tabs = self.get_tabs()
        for tab in tabs:
            self.close_tab(tab.get("id"))
            time.sleep(1)
        return True

    def get_info(self):
        try:
            response = requests.get(f'http://localhost:{self.config.debug_port}/json/version', timeout=0.2)
            info = response.json()
            return info
        except Exception as e:
            return None

    def activate_tab(self, tab_id):
        """
        激活指定的标签页
        """
        try:
            url = f" http://localhost:{self.config.debug_port}/json/activate/{tab_id}"
            response = requests.get(url)
            if not response.status_code == 200:
                logger.error(f"激活标签页失败: {response.text}")
        except Exception as e:
            logger.error(f"激活标签页时出错: {e}")

    def browser_interactive(self, payload_list = [{}]) -> bool:
        '''
        浏览器交互功能
        '''
        try:
            tabs = self.get_tabs()
            if tabs is not None:
                if len(tabs) == 0:
                    _ = requests.put(f'http://localhost:{self.config.debug_port}/json/new', timeout=1)
                tabs = self.get_tabs()
                if len(tabs) > 0:
                    ws_url = tabs[0].get("webSocketDebuggerUrl", None)
                    if ws_url:
                        ws = websocket.WebSocket()
                        ws.connect(ws_url)
                        for payload in payload_list:
                            self.message_id += 1
                            payload["id"] = self.message_id
                            ws.send(json.dumps(payload))
                            result = ws.recv()
                            logger.info(f"Chrome CDP {payload.get('method')} 响应: {result}")
                        ws.close()
            return True
        except Exception as e:
            logger.error(f"Chrome CDP 命令失败: {e}")
            return False
        
        
    def navigate_url(self, url: str = "about:blank"):
        '''
        浏览网页，检查浏览器的tabs ，如果已经打开，直接返回True
        否则，尝试浏览指定url，返回True
        '''

        tabs = self.get_tabs()
        if tabs is None:
            # 尝试启动浏览器
            self._start_browser(url)
            tabs = self.get_tabs()
            if tabs is None:
                logger.error(f"启动浏览器失败")
                return False 
            return True

        def url_is_opened(url:str):
            for tab in tabs:
                if url in tab.get("url"):
                    self.activate_tab(tab.get("id"))
                    return True
            return False

        if url_is_opened(url):
            payload = {
                "id": self.message_id, 
                "method": "Page.reload", 
                "params": {
                    "ignoreCache": False
                    }
                }
            return self.browser_interactive([payload])

        payload = {
            "id": self.message_id,
            "method": "Page.navigate",
            "params": {
                "url": url
            }
        }
        return self.browser_interactive([payload])


    def navigate_keypress(self, key, code):
        payload_list = []
        payload_list.append(
            {
                "id": self.message_id,
                "method": "Input.dispatchKeyEvent",
                "params": {
                    "type": "keyDown",
                    "key": key,
                    "code": code
                }
            })      
        payload_list.append(
            {
                "id": self.message_id,
                "method": "Input.dispatchKeyEvent",
                "params": {
                    "type": "keyUp",
                    "key": key,
                    "code": code
                }
            })
        self.browser_interactive(payload_list)


def open_url(url:str) -> dict[str, str]:
    logger.info(f"启动Chrome浏览器, 打开链接: {url}")
    wp = WebPlayer()
    if not wp.navigate_url(url):
        return {"result": "fail"}
    return {"result": "success"}

def close_browser():
    wp = WebPlayer()
    return wp.close_browser()

def get_status():
    wp = WebPlayer()
    return asdict(wp.get_status())