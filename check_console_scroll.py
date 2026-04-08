"""SE 콘솔 위로 스크롤해서 전체 로그 확인"""
import ctypes
import time
import win32gui
import win32con
from PIL import ImageGrab
import os

# SpaceEngine 창 찾기
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

# 콘솔 열기
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
time.sleep(1)

# Page Up으로 위로 스크롤
for i in range(5):
    ctypes.windll.user32.keybd_event(win32con.VK_PRIOR, 0, 0, 0)  # Page Up
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(win32con.VK_PRIOR, 0, 2, 0)
    time.sleep(0.3)

time.sleep(0.5)

# 스크린샷 1 (상단)
rect = win32gui.GetWindowRect(hwnd)
img1 = ImageGrab.grab(bbox=rect)
out1 = os.path.join(os.path.dirname(__file__), "se_console_top.png")
img1.save(out1)
print(f"상단 스크린샷: {out1}")

# Page Down으로 중간으로
for i in range(2):
    ctypes.windll.user32.keybd_event(win32con.VK_NEXT, 0, 0, 0)  # Page Down
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(win32con.VK_NEXT, 0, 2, 0)
    time.sleep(0.3)

time.sleep(0.5)

# 스크린샷 2 (중간)
img2 = ImageGrab.grab(bbox=rect)
out2 = os.path.join(os.path.dirname(__file__), "se_console_mid.png")
img2.save(out2)
print(f"중간 스크린샷: {out2}")

# 콘솔 닫기
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
