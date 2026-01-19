import subprocess
import pyautogui
import time

def play_ppt(url, start_page=1):
    subprocess.Popen([
        "ksolaunch",
        url
    ])
    time.sleep(5)
    pyautogui.press("f5")
    for _ in range(start_page - 1):
        pyautogui.press("pagedown")

def next_page():
    pyautogui.press("pagedown")

def prev_page():
    pyautogui.press("pageup")
