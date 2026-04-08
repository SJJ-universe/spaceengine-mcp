"""콘솔이 열려있으면 확실히 닫기 — Enter로 입력 해제 후 tilde"""
from src.spaceengine_mcp.bridges.console_bridge import (
    find_se_window, _toggle_console, _press_enter, _clear_input
)
import win32gui, win32con, win32api, time

hwnd = find_se_window()
if hwnd:
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    # 1) 콘솔 입력에 남은 텍스트 지우기
    _clear_input(hwnd)
    time.sleep(0.1)
    # 2) Enter로 빈 입력 제출 (콘솔이 열려있으면 아무 효과 없음)
    _press_enter(hwnd)
    time.sleep(0.2)
    # 3) Tilde로 콘솔 닫기
    _toggle_console(hwnd)
    time.sleep(0.3)
    # 4) 한번 더 tilde (혹시 방금 열린 거면 닫기)
    # 현재 상태를 모르므로 2번 더 안전하게
    print("Console close attempted")
else:
    print("SE window not found")
