import platform
import socket
from typing import Dict
from dataclasses import dataclass, field, asdict
from system.device_status import get_network_status  

@dataclass
class SystemAttributes:
    platform: str = ""
    hostname: str = ""
    abilities: Dict[str, str] = field(default_factory=dict)

def get_device_attributes():
    attr = SystemAttributes()
    attr.platform = platform.platform()
    attr.hostname = socket.gethostname()
    attr.abilities = {
        "ppt": True,
        "video": True,
        "web": True
    }
    return asdict(attr)
