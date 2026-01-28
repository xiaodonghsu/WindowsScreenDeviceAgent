from typing import Literal
import os
import subprocess
import psutil
from pyautogui import FailSafeException
from common.config import load_config
import requests
import websocket
import json
import time
import logging
logger = logging.getLogger(__name__)

class WebPlayer:
    def __init__(self, browser_exe_file:str="", debug_port:int=9222):
        if browser_exe_file == "":
            config = load_config()
            config = config.get("config", {})
            browser_exe_file= config.get("player", {}).get("browser", {}).get("exe", "")
            debug_port:int = config.get("player", {}).get("browser", {}).get("cdp_port", 9222)
        if browser_exe_file is None:
            raise ValueError("Browser path must be specified in config.yaml.")
        if os.path.exists(browser_exe_file) is False:
            raise ValueError(f"Browser path does not exist: {browser_exe_file}")
        self.browser_exe_file: str = browser_exe_file
        self.debug_port: int = debug_port
        self.message_id: int = 0
        self.browser_info = None

    def start_browser(self, url:str="about:blank") -> bool:
        '''
        检查浏览器是否已经打开,如果没有打开,则打开浏览器
        如果已经打开,则检查是否有指定的url,如果没有,则打开url
        '''
        # 直接读取9222端口来测试
        info = self.get_info()
        if info is None:
            # 检查同类型的浏览器已经打开,如果有必须关闭
            logger.info("__关闭可能已经打开的浏览器")
            self.__close_browser()
            # 启动浏览器
            logger.info("__启动浏览器")
            self.__start_browser(url)

        info = self.get_info()
        if info is None:
            return False
        return True

    def __start_browser(self, url="about:blank"):
        os_temp_dir = os.environ.get("TEMP")
        cmdline = [
            f'{self.browser_exe_file}',
            "--start-fullscreen",
            f"--remote-debugging-port={self.debug_port}",
            "--remote-allow-origins=*",
            f'--user-data-dir={os_temp_dir}',
            "--UseBasicParsing",
            url
            ]
        logger.info(f"启动浏览器: {' '.join(cmdline)}")
        subprocess.Popen(cmdline)

    def __close_browser(self):
        browser_name = os.path.basename(self.browser_exe_file).lower()
        try:
            for process in psutil.process_iter():
                if process.name().lower() == browser_name:
                    logger.info(f"终止进程: {process.pid} - {process.nameline()}")
                    process.terminate()
                    time.sleep(1)
        except:
            pass

    def get_tabs(self):
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=0.5)
            tabs = response.json()
            return tabs
        except Exception as e:
            logger.error(e)
            return None

    def get_info(self):
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json/version', timeout=0.2)
            info = response.json()
            return info
        except Exception as e:
            logger.error(e)
            return None

    def activate_tab(self, tab_id):
        """
        激活指定的标签页
        """
        try:
            url = f" http://localhost:{self.debug_port}/json/activate/{tab_id}"
            response = requests.get(url)
            if not response.status_code == 200:
                logger.error(f"激活标签页失败: {response.text}")
        except Exception as e:
            logger.error(f"激活标签页时出错: {e}")


    def browser_interactive(self, payload_list = [{}]):
        '''

        浏览器交互功能

        '''
        try:
            tabs = self.get_tabs()
            if tabs is not None:
                ws_url = tabs[0].get("webSocketDebuggerUrl", None)
                if ws_url:
                    logger.info(f"连接到 WebSocket: {ws_url}")
                    ws = websocket.WebSocket()
                    ws.connect(ws_url)
                    for payload in payload_list:
                        self.message_id += 1
                        payload["id"] = self.message_id
                        ws.send(json.dumps(payload))
                        result = ws.recv()
                        logger.info(f"{payload.get('method')} 响应: {result}")
                    ws.close()
            return True
        except Exception as e:
            logger.error(f"打开URL时出错: {e}")
            return False
        
        
    def navigate_url(self, url="about:blank"):
        '''
        浏览网页，检查浏览器的tabs ，如果已经打开，直接返回True
        否则，尝试浏览指定url，返回True
        '''

        tabs = self.get_tabs()
        if tabs is None:
            return False

        def url_is_opened(url:str):
            for tab in tabs:
                if url in tab.get("url"):
                    self.activate_tab(tab.get("id"))
                    return True
            return False

        if url_is_opened(url):
            return True

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
    logger.info("浏览网页", url)
    wp = WebPlayer()
    if not wp.start_browser(url):
        return {"result": "fail"}
    if not wp.navigate_url(url):
        return {"result": "fail"}
    return {"result": "success"}

