"""SE 콘솔 마우스 휠로 스크롤 + 스크린샷"""
import ctypes
import time
import win32gui
import win32con
import win32api
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

rect = win32gui.GetWindowRect(hwnd)
# 콘솔 영역 위에 마우스 커서 위치시키기 (창 중앙 상단)
cx = (rect[0] + rect[2]) // 2
cy = rect[1] + (rect[3] - rect[1]) // 3
win32api.SetCursorPos((cx, cy))
time.sleep(0.3)

# 마우스 휠 위로 스크롤 (WHEEL_DELTA = 120)
WHEEL_UP = 120
for i in range(20):
    lparam = win32api.MAKELONG(cx, cy)
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, WHEEL_UP, 0)  # MOUSEEVENTF_WHEEL
    time.sleep(0.1)

time.sleep(0.5)

img1 = ImageGrab.grab(bbox=rect)
out1 = os.path.join(os.path.dirname(__file__), "se_console_scroll1.png")
img1.save(out1)
print(f"스크롤 상단: {out1}")

# 조금 아래로
for i in range(8):
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, -WHEEL_UP, 0)
    time.sleep(0.1)

time.sleep(0.5)

img2 = ImageGrab.grab(bbox=rect)
out2 = os.path.join(os.path.dirname(__file__), "se_console_scroll2.png")
img2.save(out2)
print(f"스크롤 중간: {out2}")

# 콘솔 닫기
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
