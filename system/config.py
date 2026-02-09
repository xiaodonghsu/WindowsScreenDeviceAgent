import winreg
import shutil

def find_app_path(exe):
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
        ) as k:
            return winreg.QueryValue(k, None)
    except FileNotFoundError:
        return None

def get_app_path(exe):
    app_path = shutil.which(exe)
    if app_path:
        return app_path
    app_path = find_app_path(exe)
    if app_path:
        return app_path

CONFIG = {
    "slideplayer": {
    },
    "browser": {
      "exe": "chrome.exe",
      "exe_args": [
        "--start-fullscreen",
        "--remote-debugging-port=9222",
        "--user-data-dir=%TEMP%\\ChromeDevSession",
        "--remote-allow-origins=*"
      ],
      "cdp_port": 9222
    },
    "videoplayer": {
      "exe": "vlc.exe",
      "host": "127.0.0.1",
      "port": 9999
    },
    "avatarplayer": {
      "exe": "avatar-player 1.0.0.exe",
      "host": "127.0.0.1",
      "port": 6789
    }
}