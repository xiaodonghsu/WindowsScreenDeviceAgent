import psutil
import socket
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict
# from system.device_attr import get_device_info

# def collect_status():
#     return get_device_info()

# Get disk usage information
def get_disk_usage():
    d = psutil.disk_usage("/")
    return {
        "total": d.total,
        "used": d.used,
        "free": d.free,
        "percent": d.percent,
    }

# 获取网络接口状态
def get_network_status() -> dict[Any, Any]:
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    interfaces = {}
    for if_name, addrs in net_if_addrs.items():
        stats = net_if_stats.get(if_name)
        interfaces[if_name] = {
            "isup": stats.isup if stats else False,
            "speed": stats.speed if stats else 0,
            "addresses": [addr.address for addr in addrs if addr.family == psutil.AF_LINK or addr.family == socket.AF_INET]
        }
    return interfaces

# 获取所有运行中的进程信息
def get_running_processes():
    processes = []
    for proc in psutil.process_iter():
        try:
            p = proc.as_dict(attrs=['pid', 'name', 'create_time', 'cwd'])
            p['status'] = proc.status()
            p['memory'] = proc.memory_percent()
            p['cpu'] = proc.cpu_percent()
            processes.append(p)
        except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    return processes

# 通过API获取PPT播放器的信息
def get_slide_player_status():
    from player.slide_player import SlidePlayerController
    slide_player = SlidePlayerController()
    return slide_player.detect_status()


@dataclass
class DeviceStatus:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    network: Dict[str, str] = field(default_factory=dict)

def get_device_status():
    status = DeviceStatus()
    status.cpu_percent = psutil.cpu_percent()
    status.memory_percent = psutil.virtual_memory().percent
    status.network = get_network_status()
    return asdict(status)