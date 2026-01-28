import requests
import json
from dotenv import load_dotenv
from common import get_device_name
from common.config import CONFIG_FILE
ASSETS_FILE = "assets.json"

def get_cms_baseurl(key:str="CMS_BASEURL") -> str | None:
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

def load_assets(assets_path:str=ASSETS_FILE):
    try:
        with open(assets_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def get_cms_token(cms_baseurl:str="") -> str:
    # 提取 cms_token
    # curl  http://192.168.41.135:1337/api/access-token
    if cms_baseurl == "":
        cms_baseurl, _ = load_env()
        if cms_baseurl == "":
            raise Exception("CMS base URL not found")
    url: str = f"{cms_baseurl}/access-token"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    response_json = response.json()
    if response_json.get("data", None) is None:
        return None
    if response_json.get("data", None).get("token", "") == "":
        return None
    cms_token =response_json.get("data", None).get("token", "") 
    return cms_token

def download_config(cms_baseurl:str="", device_name:str="", cms_token:str="", config_path:str=CONFIG_FILE):
    if cms_baseurl == "":
        cms_baseurl =  get_cms_baseurl()
    if device_name == "":
        device_name = get_device_name()
    if cms_token == "":
        cms_token = get_cms_token(cms_baseurl)
    # 构造URL 类似: http://{{host}}:{{port}}/api/screens?filters[name][$eq]=xxxx
    # curl --location 'http://192.168.41.135:1337/api/screens?filters[name][$eq]=screen-d16' \
    # --header 'Authorization: Bearer xxxx'

    url: str = f"{cms_baseurl}/screens"
    params = {
        "filters[name][$eq]": device_name
    }
    headers: dict = {'Authorization': f'Bearer {cms_token}'}

    # 发送请求
    # response = requests.get(url=url, headers=headers)
    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code != 200:
        return None
    response_json = response.json()
    if response_json.get("data", []) == []:
        return None
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(response_json.get("data")[0], f, ensure_ascii=False)

    return response_json.get("data")[0]

def download_assets(cms_baseurl:str="", device_name:str="", scene_name:str="default", cms_token:str="", assets_file = ASSETS_FILE):
    '''
    从CMS下载当前设备指定场景的配置资源文件
    '''
    if cms_baseurl == "":
        cms_baseurl = get_cms_baseurl() 
    if device_name == "":
        device_name = get_device_name()
    if cms_token == "":
        cms_token = get_cms_token(cms_baseurl)

    # 从 cms_baseurl 的中获取根路径 http://192.168.41.135:1337
    root_url = "/".join(cms_baseurl.split("/")[:3])


    url: str = f"{cms_baseurl}/screen-scene-assets"
    params = {
        "filters[screen][name][$eq]": device_name,
        "filters[scene][name][$eq]": scene_name,
        "sort": "order:asc",
        "populate[asset][populate]": "media"
    }
    headers: dict = {'Authorization': f'Bearer {cms_token}'}

    # 发送请求
    # response = requests.get(url=url, headers=headers)
    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code != 200:
        return None
    response_json = response.json()
    if response_json.get("data", []) == []:
        return None
    assets_data = {"scene": scene_name, "assets": []}
    for item in response_json.get("data", []):
        key = item["asset"]["name"]
        item_type = item["asset"]["type"]
        item_url = ""
        if item["asset"]["media"] is None:
            item_url = item["asset"]["url"]
        else:
            item_url = root_url + item["asset"]["media"]["url"]
        item_config = item["asset"].get("config", {})
        local_file = ""

        # 如果item_type 不是 webpage, 将文件下载到本地临时目录中
        if item_type != "webpage":
            # 下载文件到临时目录中
            local_file = download_file(item_url)

        assets_data["assets"].append({"name": key,
                            "type": item_type,
                            "url": item_url,
                            "file": local_file,
                            "config": item_config})
    with open(assets_file, "w", encoding="utf-8") as f:
        json.dump(assets_data, f,ensure_ascii=False)
    return assets_data

def download_file(url: str) -> str:
    """Download file from URL and save it to temporary directory"""
    import os
    import tempfile
    import requests
    
    temp_dir = tempfile.gettempdir()
    local_file = os.path.join(temp_dir, url.split("/")[-1])
    if os.path.exists(local_file):
        return local_file
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_file, 'wb', encoding='utf-8') as f:
            f.write(response.content)
        return local_file
    return ""