from screeninfo import get_monitors
import win32gui
import win32process
import win32con
from screeninfo import get_monitors
import time

def list_monitors():
    """
    返回显示器列表（含坐标），Windows 多屏会有负坐标（例如副屏在左侧）
    """
    mons = get_monitors()
    out = []
    for i, m in enumerate(mons):
        # m.x, m.y 是左上角坐标；m.width, m.height 是分辨率
        out.append({
            "index": i,
            "x": m.x,
            "y": m.y,
            "width": m.width,
            "height": m.height,
            "name": getattr(m, "name", "")
        })
    return out

def move_window_to_monitor(hwnd: int, monitor_index: int, make_topmost: bool = False):
    mons = list_monitors()
    if monitor_index < 0 or monitor_index >= len(mons):
        raise ValueError(f"monitor_index out of range: {monitor_index}, total={len(mons)}")

    m = mons[monitor_index]
    x, y, w, h = m["x"], m["y"], m["width"], m["height"]

    # 先恢复窗口（否则某些全屏/最大化状态移动不生效）
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    flags = win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW
    if make_topmost:
        # 让窗口置顶（可选）
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, w, h, flags)
    else:
        win32gui.SetWindowPos(hwnd, None, x, y, w, h, flags)


def find_main_window_by_pid(pid: int, timeout: float = 5.0) -> int:
    """
    在给定 timeout 内，找到该 pid 的“主窗口”句柄（VLC 窗口通常是 'VLC media player'）
    """
    end = time.time() + timeout
    found = {"hwnd": 0}

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
        if window_pid != pid:
            return
        # 过滤掉无标题/工具窗口
        title = win32gui.GetWindowText(hwnd)
        if title:
            found["hwnd"] = hwnd

    while time.time() < end:
        win32gui.EnumWindows(enum_handler, None)
        if found["hwnd"]:
            return found["hwnd"]
        time.sleep(0.05)

    raise RuntimeError("Cannot find VLC main window by pid (timeout).")
