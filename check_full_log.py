"""SE 콘솔 전체 스크롤 스크린샷 — 여러 장"""
import ctypes
import time
import win32gui
import win32api
from PIL import ImageGrab
import os

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

rect = win32gui.GetWindowRect(hwnd)
cx = (rect[0] + rect[2]) // 2
cy = rect[1] + (rect[3] - rect[1]) // 3

# 최상단으로 스크롤
for i in range(50):
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, 120, 0)
    time.sleep(0.05)
time.sleep(0.5)

# 5장 캡처 (위에서부터)
for shot in range(5):
    img = ImageGrab.grab(bbox=rect)
    out = os.path.join(os.path.dirname(__file__), f"se_log_{shot+1}.png")
    img.save(out)
    print(f"Shot {shot+1}: {out}")
    
    # 아래로 스크롤
    for i in range(8):
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, -120, 0)
        time.sleep(0.05)
    time.sleep(0.3)

# 콘솔 닫기
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
