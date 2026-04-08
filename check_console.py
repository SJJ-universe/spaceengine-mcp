"""SE 콘솔 열기 + 스크린샷 캡처 — 에러 확인용"""
import ctypes
import time
import win32gui

# SpaceEngine 창 찾기 (타이틀에 해상도 포함됨)
hwnd = None
def find_se(h, _):
    global hwnd
    title = win32gui.GetWindowText(h)
    if title.startswith("SpaceEngine"):
        hwnd = h
win32gui.EnumWindows(find_se, None)

if not hwnd:
    print("SpaceEngine 창을 찾을 수 없음")
    exit(1)

win32gui.SetForegroundWindow(hwnd)
time.sleep(0.3)

# Tilde 키로 콘솔 토글 (열기)
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
time.sleep(1.5)

# 스크린샷 캡처
from PIL import ImageGrab
import os

rect = win32gui.GetWindowRect(hwnd)
img = ImageGrab.grab(bbox=rect)
out = os.path.join(os.path.dirname(__file__), "se_console_check.png")
img.save(out)
print(f"스크린샷 저장: {out}")

# 콘솔 닫기
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
