# from __future__ import annotations

'''
使用Python语言生成在windows中slide_player的功能：
1、尽量使用 win32com.client 的相关能力，方便后续维护；
2、slide_player 的应用程序包括："Kwpp.Application"，"PowerPoint.Application"，其中Kwpp.Application优先；
3、功能包括：
  - 应用程序状态检测功能
    - 检测应用程序是否启动
    - 应用程序启动时:
      - 应用程序的名字
      - 当前打开的文件路径
      - 当前页面的页码
      - 当前是否在播放状态
      - 当前播放的页码
  - 播放控制功能
    - 开始播放：指定播放的文件名和起始页码（默认第一页）
    - 下一页（要求循环播放能力: 如果当前是最后一页，则跳转到第一页）
    - 上一页（要求循环播放能力: 如果当前是第一页，则跳转到最后一页）
    - 停止播放：退出应用程序

'''


# OLD IMPLEMENTATION USING pyautogui AND subprocess


# import subprocess
# import pyautogui
# import time



# self.__slide_app_list = ["PowerPoint.Application", "Kwpp.Application"]

# def play_ppt(url, start_page=1):
#     subprocess.Popen([
#         "ksolaunch",
#         url
#     ])
#     time.sleep(5)
#     pyautogui.press("f5")
#     for _ in range(start_page - 1):
#         pyautogui.press("pagedown")

# def next_page():
#     pyautogui.press("pagedown")

# def prev_page():
#     pyautogui.press("pageup")


# VERSION USING win32com.client

"""Slide player control for Windows PowerPoint/WPS (Kwpp)."""

import os
from dataclasses import dataclass
from typing import Optional

import pywintypes
import win32com.client


APP_PROGIDS = ("Kwpp.Application", "PowerPoint.Application")


@dataclass
class SlidePlayerStatus:
    is_running: bool
    is_visible: bool
    app_name: Optional[str] = None
    file_path: Optional[str] = None
    current_slide_index: Optional[int] = None
    is_presenting: Optional[bool] = None
    current_show_slide_index: Optional[int] = None


class SlidePlayerController:
    """Controls slide playback for supported Windows presentation apps."""

    def __init__(self, prefer_kwpp: bool = True) -> None:
        self._progids = APP_PROGIDS if prefer_kwpp else APP_PROGIDS[::-1]

    def _get_running_app(self):
        for progid in self._progids:
            try:
                return win32com.client.GetActiveObject(progid), progid
            except pywintypes.com_error:
                continue
        return None, None

    def _dispatch_app(self, progid: str):
        return win32com.client.Dispatch(progid)

    def _get_or_start_app(self):
        app, progid = self._get_running_app()
        if app is not None:
            if app.Visible == 0:
                app.Visible = True
            return app, progid
        for progid in self._progids:
            try:
                return self._dispatch_app(progid), progid
            except pywintypes.com_error:
                continue
        raise RuntimeError("Unable to start a slide player application.")

    def _get_active_presentation(self, app):
        try:
            return app.ActivePresentation
        except pywintypes.com_error:
            pass
        try:
            if app.Presentations.Count > 0:
                return app.Presentations(1)
        except pywintypes.com_error:
            return None
        return None

    def _get_presentation_by_path(self, app, file_path: str):
        normalized = os.path.normcase(os.path.abspath(file_path))
        try:
            for idx in range(1, app.Presentations.Count + 1):
                presentation = app.Presentations(idx)
                if os.path.normcase(presentation.FullName) == normalized:
                    return presentation
        except pywintypes.com_error:
            return None
        return None

    def _get_active_window_slide_index(self, app) -> Optional[int]:
        try:
            return int(app.ActiveWindow.View.Slide.SlideIndex)
        except pywintypes.com_error:
            return None

    def _get_show_state(self, app):
        try:
            if app.SlideShowWindows.Count > 0:
                show_window = app.SlideShowWindows(1)
                return True, int(show_window.View.CurrentShowPosition)
        except pywintypes.com_error:
            return False, None
        return False, None

    def get_status(self) -> SlidePlayerStatus:
        app, progid = self._get_running_app()
        if app is None:
            return SlidePlayerStatus(is_running=False)

        is_visible: bool = False if app.Visible == 0 else True

        presentation = self._get_active_presentation(app)
        file_path = None
        if presentation is not None:
            try:
                file_path = presentation.FullName
            except pywintypes.com_error:
                file_path = None

        current_slide_index = self._get_active_window_slide_index(app)
        is_presenting, show_slide_index = self._get_show_state(app)

        return SlidePlayerStatus(
            is_running=True,
            is_visible=is_visible,
            app_name=progid,
            file_path=file_path,
            current_slide_index=current_slide_index,
            is_presenting=is_presenting,
            current_show_slide_index=show_slide_index,
        )

    def start_play(self, file_path: str, start_slide: int = 1) -> None:
        app, _ = self._get_or_start_app()
        presentation = self._get_presentation_by_path(app, file_path)
        if presentation is None:
            presentation = app.Presentations.Open(file_path, WithWindow=True)
        try:
            presentation.Windows(1).Activate()
        except pywintypes.com_error:
            pass

        settings = presentation.SlideShowSettings
        settings.StartingSlide = int(start_slide)
        settings.Run()

    def next_slide(self) -> None:
        app, _ = self._get_or_start_app()
        presentation = self._get_active_presentation(app)
        if presentation is None:
            raise RuntimeError("No active presentation is open.")

        is_presenting, show_slide_index = self._get_show_state(app)
        total_slides = int(presentation.Slides.Count)
        if not is_presenting:
            raise RuntimeError("Slide show is not currently running.")

        target = 1 if show_slide_index >= total_slides else show_slide_index + 1
        app.SlideShowWindows(1).View.GotoSlide(target)

    def previous_slide(self) -> None:
        app, _ = self._get_or_start_app()
        presentation = self._get_active_presentation(app)
        if presentation is None:
            raise RuntimeError("No active presentation is open.")

        is_presenting, show_slide_index = self._get_show_state(app)
        total_slides = int(presentation.Slides.Count)
        if not is_presenting:
            raise RuntimeError("Slide show is not currently running.")

        target = total_slides if show_slide_index <= 1 else show_slide_index - 1
        app.SlideShowWindows(1).View.GotoSlide(target)

    def stop_play(self) -> None:
        app, _ = self._get_running_app()
        if app is None:
            return
        app.Quit()

def get_status():
    controller = SlidePlayerController()
    return controller.get_status()

def play_ppt(slide_file: str, start_page: int = 1):
    controller = SlidePlayerController()
    controller.start_play(file_path=slide_file, start_slide=start_page)

def next_page():
    controller = SlidePlayerController()
    controller.next_slide()

def prev_page():
    controller = SlidePlayerController()
    controller.previous_slide()