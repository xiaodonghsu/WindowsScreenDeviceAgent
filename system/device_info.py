import platform
import socket

def get_device_attributes():
    return {
        "deviceType": "screen",
        "os": platform.platform(),
        "hostname": socket.gethostname(),
        "support": {
            "ppt": True,
            "video": True,
            "web": True
        }
    }
