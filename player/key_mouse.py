import pyautogui
import logging
from common.config import get_device_name
logger = logging.getLogger(get_device_name())

def key_press(key: str | list[str]):
    """
    模拟键盘按键
    
    Args:
        key: 按键名称，支持的按键包括：
            - 字母数字键: 'a', '1', 'space', 'enter' 等
            - 功能键: 'ctrl', 'shift', 'alt', 'win' 等
            - 方向键: 'up', 'down', 'left', 'right'
            - 特殊键: 'esc', 'tab', 'delete', 'backspace' 等
            组合键调用，如: key_press(['ctrl', 'c'])
    """

    try:
        if type(key) == list:
            logger.info(f"组合键调用: {key}")
            pyautogui.hotkey(*key)
        else:
            logger.info(f"单键调用: {key}")
            pyautogui.press(key)
    except Exception as e:
        logger.error(f"按键失败: {key}, 错误: {str(e)}")
