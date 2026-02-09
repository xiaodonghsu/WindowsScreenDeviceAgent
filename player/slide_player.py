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
"""Slide player control for Windows PowerPoint/WPS (Kwpp)."""

from logging import Logger


import os
from dataclasses import dataclass, asdict
from typing import Optional

import pywintypes
import win32com.client
import pythoncom
import logging
from common.config import get_device_name
logger: Logger = logging.getLogger(get_device_name())

APP_PROGIDS = ("Kwpp.Application", "PowerPoint.Application")


@dataclass
class SlidePlayerStatus:
    is_running: bool = False
    is_visible: bool = False
    app_name: Optional[str] = None
    file_path: Optional[str] = None
    current_slide_index: Optional[int] = None
    is_presenting: Optional[bool] = None
    current_show_slide_index: Optional[int] = None


class SlidePlayerController:
    """Controls slide playback for supported Windows presentation apps."""

    def __init__(self, prefer_kwpp: bool = True) -> None:
        pythoncom.CoInitialize()
        self._progids = APP_PROGIDS if prefer_kwpp else APP_PROGIDS[::-1]

    def _get_running_app(self):
        '''
        获取当前正在运行的应用程序对象和程序的名字，如果没有，则返回None
        '''
        for progid in self._progids:
            try:
                return win32com.client.GetActiveObject(progid), progid
            except Exception as e:
                # logger.warning(f"尝试获取正在运行的{progid}失败: {e}")
                pass
        return None, None

    def _dispatch_app(self, progid: str):
        '''
        COM方式启动应用程序并返回应用程序对象
        '''
        return win32com.client.Dispatch(progid)

    def _get_or_start_app(self):
        '''
        获取当前正在运行的应用程序;
        如果没有正在运行的应用程序，则按顺序启动应用程序
        '''
        app, progid = self._get_running_app()
        if app is not None:
            if app.Visible == 0:
                app.Visible = True
            return app, progid

        logger.info(f"没有正在运行的slide程序, 尝试启动slide程序")

        for progid in self._progids:
            try:
                return self._dispatch_app(progid), progid
            except Exception as e:
                logger.info(f"尝试启动{progid}失败: {e}")
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
        status = SlidePlayerStatus()
        app, progid = self._get_running_app()

        if app is None:
            status.is_running = False
            return status
        status.is_running = True
        status.app_name = progid
        status.is_visible: bool = False if app.Visible == 0 else True

        presentation = self._get_active_presentation(app)
        if presentation is not None:
            try:
                status.file_path = presentation.FullName
            except pywintypes.com_error:
                pass
        status.current_slide_index = self._get_active_window_slide_index(app)
        status.is_presenting, status.current_show_slide_index = self._get_show_state(app)
        return status

    def start_play(self, file_path: str, start_slide: int = 1) -> None:
        # 获取slide应用程序对象
        app, _ = self._get_or_start_app()
        if app is None:
            return
        # 检查需要播放的文件是否已经加载
        presentation = self._get_presentation_by_path(app, file_path)
        if presentation is None:
            # 没有加载则加载
            presentation = app.Presentations.Open(file_path, WithWindow=True)
        try:
            # 否则直接激活窗口
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
    return asdict(controller.get_status())

def play_slide(url: str, startPage: int = 1):
    controller = SlidePlayerController()
    controller.start_play(file_path=url, start_slide=startPage)

def next_page():
    controller = SlidePlayerController()
    controller.next_slide()

def prev_page():
    controller = SlidePlayerController()
    controller.previous_slide()

def stop_slide(url: str, startPage: int = 1):
    controller = SlidePlayerController()
    controller.start_play(file_path=url, start_slide=startPage)