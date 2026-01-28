import json
from dotenv import load_dotenv
CONFIG_FILE = "config.json"


def get_device_name(key:str="IOT_DEVICE_NAME") -> str | None:
    # 读取环境变量参数
    import os
    val = ""
    if not os.getenv(key) is None:
        val = os.getenv(key)
        return val  
    _ = load_dotenv()
    if not os.getenv(key) is None:
        val = os.getenv(key)
        return val  
    return None

def load_config(config_path:str=CONFIG_FILE):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None
