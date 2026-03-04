import platform
import socket
from typing import Dict
from dataclasses import dataclass, field, asdict
import win32api
import os

@dataclass
class SystemAttributes:
    platform: str = ""
    hostname: str = ""
    agent_version: str = "0.0.0.0"
    updater_version: str = "0.0.0.0"
    abilities: Dict[str, str] = field(default_factory=dict)


def get_file_version(file_path):
    if not os.path.exists(file_path):
        return "0.0.0.0"
    info = win32api.GetFileVersionInfo(file_path, "\\")
    ms = info['FileVersionMS']
    ls = info['FileVersionLS']
    version = "%d.%d.%d.%d" % (
        win32api.HIWORD(ms),
        win32api.LOWORD(ms),
        win32api.HIWORD(ls),
        win32api.LOWORD(ls)
    )
    return version

def get_device_attributes():
    attr = SystemAttributes()
    attr.platform = platform.platform()
    attr.hostname = socket.gethostname()
    attr.agent_version = get_file_version("ExpoAgent.exe")
    attr.updater_version = get_file_version("ExpoAgentUpdater.exe")
    attr.abilities = {
        "ppt": True,
        "video": True,
        "web": True
    }
    return asdict(attr)
