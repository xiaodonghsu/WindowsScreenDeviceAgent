import psutil
import time

def collect_status():
    return {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "online": True,
        "ts": int(time.time() * 1000)
    }
