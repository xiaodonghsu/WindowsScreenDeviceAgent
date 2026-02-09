import logging
from cms import load_program
from common.config import get_device_name
logger = logging.getLogger(get_device_name())

def play_program(asset: str | int = None, start_pause=False) -> None:
    if asset is None:
        # 不指明资源, 播放第一个
        asset = 0

    if type(asset) is int:  # 如果asset是int, 认为是资源索引, 则从assets中取出对应的资源
        assets = load_program()
        assets = assets.get("assets", [])
        if asset > len(assets):
            logger.error(f"资源索引超出范围: {asset}")
            return None
        asset = assets[asset]
    else:   # 如果asset是str, 认为是资源名称, 则从assets中取出对应的资源
        assets = load_program()
        for item in assets.get("assets", []):
            if item.get("name") == asset:
                asset = item
                break

    if asset:
        logger.info(f"播放资源: {asset}")
        if asset.get("type", "") == "video":
            # 播放视频
            logger.info(f"播放视频: {asset.get('file', '')}")
            from player import play_video
            play_video(asset.get("file", ""), start_pause)
        elif asset.get("type", "") == "slide":
            # 播放幻灯片
            logger.info(f"播放幻灯片: {asset.get('file', '')}")
            from player import play_slide
            play_slide(asset.get("file", ""))
        elif asset.get("type", "") == "image":
            # 浏览网页(使用 webbrowser 播放)
            logger.info(f"浏览图片: {asset.get('file', '')}")
            from player import open_url
            open_url(asset.get("file", ""))
        elif asset.get("type", "") == "webpage":
            # 浏览网页
            logger.info(f"浏览网页: {asset.get('url', '')}")
            from player import open_url
            open_url(asset.get("url", ""))
        else:
            logger.warning(f"未知的资源类型: {asset.get('type', '')}")
    return True
