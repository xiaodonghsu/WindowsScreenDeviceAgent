import os
import subprocess
import psutil
import yaml
import requests
import websocket
import json
import time

class WebPlayer:
    def __init__(self, browser=None, debug_port=9222):
        if browser is None:
            with open("config.yaml", "r") as f:
                cfg = yaml.safe_load(f)
            browser = cfg.get("player", {}).get("browser", None)
        if browser is None:
            raise ValueError("Browser path must be specified either in config.yaml or as a parameter.")
        if os.path.exists(browser) is False:
            raise ValueError(f"Browser path does not exist: {browser}")
        self.browser = browser
        self.debug_port = debug_port
        self.message_id = 0

    def start_browser(self, url="about:blank"):
        # 直接读取9222端口来测试
        info = self.get_info()
        print(info)
        if info is None:
            # 检查是否又类型的浏览器已经打开,如果有必须关闭
            print("__关闭可能已经打开的浏览器")
            self.__close_browser()
            # 启动浏览器
            print("__启动浏览器")
            self.__start_browser(url)

        info = self.get_info()
        if info is None:
            return False

        tabs = self.get_tabs()
        if tabs is None:
            return False

        _url_is_opened = False
        for tab in tabs:
            if tab.get("url").startswith(url):
                self.activate_tab(tab.get("id"))
                _url_is_opened = True
            else:
                break
        if not _url_is_opened:
            self.open_url_in_tab(tabs[0].get("id"), url)

        return True

    def __start_browser(self, url="about:blank"):
        os_temp_dir = os.environ.get("TEMP")
        cmdline = [
            f'{self.browser}',
            "--start-fullscreen",
            f"--remote-debugging-port={self.debug_port}",
            "--remote-allow-origins=*",
            f'--user-data-dir={os_temp_dir}',
            url
            ]
        print(f"启动浏览器: {' '.join(cmdline)}")
        subprocess.Popen(cmdline)

    def __close_browser(self):
        browser_name = os.path.basename(self.browser).lower()
        print(browser_name)
        try:
            for process in psutil.process_iter():
                if process.name().lower() == browser_name:
                    print(f"终止进程: {process.pid} - {process.nameline()}")
                    process.terminate()
                    time.sleep(1)
        except Exception as e:
            pass

    def get_tabs(self):
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json', timeout=5)
            tabs = response.json()
            return tabs
        except Exception as e:
            # print(e)
            return None

    def get_info(self):
        try:
            response = requests.get(f'http://localhost:{self.debug_port}/json/version', timeout=5)
            info = response.json()
            return info
        except Exception as e:
            # print(e)
            return None

    def activate_tab(self, tab_id):
        """
        激活指定的标签页
        """
        try:
            url = f" http://localhost:{self.debug_port}/json/activate/ {tab_id}"
            response = requests.get(url)
            if response.status_code == 200:
                print(f"成功激活标签页: {tab_id}")
            else:
                print(f"激活标签页失败: {response.text}")
        except Exception as e:
            print(f"激活标签页时出错: {e}")


    def browser_interactive(self, payload_list = [{}]):
        try:
            tabs = self.get_tabs()
            if tabs is not None:
                ws_url = tabs[0].get("webSocketDebuggerUrl", None)
                if ws_url:
                    print(f"连接到 WebSocket: {ws_url}")
                    ws = websocket.WebSocket()
                    ws.connect(ws_url)
                    for payload in payload_list:
                        self.message_id += 1
                        payload["id"] = self.message_id
                        ws.send(json.dumps(payload))
                        result = ws.recv()
                        print(f"{payload.get('method')} 响应: {result}")
                    ws.close()
        except Exception as e:
            print(f"打开URL时出错: {e}")
        
        
    def navigate_url(self, url="about:blank"):
        payload = {
            "id": self.message_id,
            "method": "Page.navigate",
            "params": {
                "url": url
            }
        }
        self.browser_interactive([payload])

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

def open_url(url):
    wp = WebPlayer()
    print("启动浏览器")
    wp.start_browser()
    print(wp.get_info())
    wp.navigate_url(url) 

def check_chrome_devtools():
    """
    使用 Chrome DevTools Protocol 检查页面信息
    """
    try:
        # 连接到 Chrome DevTools
        response = requests.get(' http://localhost:9222/json')
        tabs = response.json()
        
        if not tabs:
            print("没有找到任何标签页")
            return False, []
        
        print(f"找到 {len(tabs)} 个标签页:")
        
        tab_info = []
        for i, tab in enumerate(tabs):
            info = {
                'id': tab.get('id'),
                'title': tab.get('title'),
                'url': tab.get('url'),
                'type': tab.get('type')
            }
            tab_info.append(info)
            print(f"{i+1}. {info['title']}")
            print(f"   URL: {info['url']}")
            print(f"   类型: {info['type']}")
            print()
        
        return True, tab_info
        
    except requests.exceptions.ConnectionError:
        print("无法连接到 Chrome DevTools。请确保 Chrome 以调试模式启动:")
        print("chrome.exe --remote-debugging-port=9222")
        return False, []
    except Exception as e:
        print(f"发生错误: {e}")
        return False, []

