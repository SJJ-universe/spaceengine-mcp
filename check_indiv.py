"""개별 테스트 후 콘솔 에러 확인 — 최상단부터 캡처"""
import ctypes, time, win32gui, win32api
from PIL import ImageGrab
import os

hwnd = None
def find_se(h, _):
    global hwnd
    if win32gui.GetWindowText(h).startswith("SpaceEngine"):
        hwnd = h
win32gui.EnumWindows(find_se, None)
if not hwnd:
    print("SE 없음"); exit(1)

win32gui.SetForegroundWindow(hwnd)
time.sleep(0.3)
ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
time.sleep(1)

rect = win32gui.GetWindowRect(hwnd)

# 최상단으로
for _ in range(80):
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, 120, 0)
    time.sleep(0.03)
time.sleep(0.5)

for shot in range(7):
    img = ImageGrab.grab(bbox=rect)
    out = os.path.join(os.path.dirname(__file__), f"se_indiv_{shot+1}.png")
    img.save(out)
    print(f"Shot {shot+1}: {out}")
    for _ in range(6):
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, -120, 0)
        time.sleep(0.05)
    time.sleep(0.3)

ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
