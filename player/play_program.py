import logging
from math import log
from cms import load_program
from common.config import get_device_name
logger = logging.getLogger(get_device_name())

def play_program(program: str | int = None, start_pause=False) -> None:
    if program is None:
        # 不指明资源, 播放第一个
        program = 0

    if type(program) is int:  # 如果program是int, 认为是资源索引, 则从programs中取出对应的资源
        programs = load_program()
        programs = programs.get("programs", [])
        if len(programs) == 0:
            logger.warning("未设定节目列表为空!")
            return None
        if program >= len(programs):
            logger.error(f"资源索引超出范围: {programs}")
            return None
        program = programs[program]
    else:   # 如果program是str, 认为是资源名称, 则从programs中取出对应的资源
        programs = load_program()
        for item in programs.get("programs", []):
            if item.get("name", "") == program:
                program = item
                break
    if program:
        logger.info(f"播放资源: {program}")
        if program.get("type", "") == "video":
            # 播放视频
            logger.info(f"播放视频: {program.get('file', '')}")
            from player import play_video
            play_video(program.get("file", ""), start_pause)
        elif program.get("type", "") == "slide":
            # 播放幻灯片
            logger.info(f"播放幻灯片: {program.get('file', '')}")
            from player import play_slide
            play_slide(program.get("file", ""))
        elif program.get("type", "") == "image":
            # 浏览网页(使用 webbrowser 播放)
            logger.info(f"浏览图片: {program.get('file', '')}")
            from player import open_url
            open_url(program.get("file", ""))
        elif program.get("type", "") == "webpage":
            # 浏览网页
            logger.info(f"浏览网页: {program.get('url', '')}")
            from player import open_url
            open_url(program.get("url", ""))
        else:
            logger.warning(f"未知的资源类型: {program.get('type', '')}")
    return True
