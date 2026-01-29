import logging
from cms import load_assets
from common import get_device_name
logger = logging.getLogger(get_device_name())

def play_asset(asset: str | int = None) -> None:
    if asset is None:
        # 不指明资源, 播放第一个
        asset = 1

    if type(asset) is int:  # 如果asset是int, 认为是资源索引, 则从assets中取出对应的资源
        assets = load_assets()
        print(assets)
        assets = assets.get("assets", [])
        if asset > len(assets):
            logger.error(f"资源索引超出范围: {asset}")
            return None
        asset = assets[asset-1]
    else:   # 如果asset是str, 认为是资源名称, 则从assets中取出对应的资源
        assets = load_assets()
        for item in assets.get("assets", []):
            if item.get("name") == asset:
                asset = item
                break

    if asset:
        logger.info(f"播放资源: {asset}")
        if asset.get("type", "") == "video":
            # 播放视频
            from player import play_video
            play_video(asset.get("file", ""))
        elif asset.get("type", "") == "slide":
            # 播放幻灯片
            from player import play_slide
            play_slide(asset.get("file", ""))
        elif asset.get("type", "") == "image":
            # 浏览网页(使用 webbrowser 播放)
            from player import open_url
            open_url(asset.get("file", ""))
        elif asset.get("type", "") == "webpage":
            # 浏览网页
            from player import open_url
            open_url(asset.get("url", ""))
        else:
            logger.warning(f"未知的资源类型: {asset.get('type', '')}")
    return True
