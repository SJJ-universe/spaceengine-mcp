"""
SpaceEngine 비행 시뮬레이터 브릿지.

키 홀드(지속 누름) 기반 비행 제어를 제공합니다.
SE 비행 모드에서 WASD로 추력, QE로 요 회전 등을 수행합니다.

핵심: _keybd_tap()은 순간 입력이므로, 비행에는 _key_hold() (지속 입력)을 사용합니다.
ESC 키 차단 유지.
"""
import logging
import time

import win32api
import win32con

from spaceengine_mcp.bridges.console_bridge import (
    find_se_window,
    KEYEVENTF_KEYUP,
    DELAY_FOREGROUND,
)

logger = logging.getLogger(__name__)

# ── 비행 키 매핑 (SE 기본 바인딩) ────────────────────────────────────────────
THRUST_KEY_MAP = {
    "forward": ord('W'),
    "backward": ord('S'),
    "left": ord('A'),
    "right": ord('D'),
    "up": win32con.VK_SPACE,
    "down": win32con.VK_CONTROL,
}

ROTATION_KEY_MAP = {
    "yaw_left": ord('Q'),
    "yaw_right": ord('E'),
    "pitch_up": win32con.VK_UP,
    "pitch_down": win32con.VK_DOWN,
    "roll_left": ord('Z'),
    "roll_right": ord('C'),
}

THROTTLE_KEYS = {
    "increase": 0xBB,  # VK_OEM_PLUS (+)
    "decrease": 0xBD,  # VK_OEM_MINUS (-)
}


def _ensure_foreground() -> int:
    """SE 창을 찾아 포어그라운드로 설정"""
    hwnd = find_se_window()
    if hwnd is None:
        raise RuntimeError("실행 중인 SpaceEngine 창��� 찾을 수 없음")
    import win32gui
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(DELAY_FOREGROUND)
    return hwnd


def _key_hold(vk: int, duration: float):
    """키를 지정 시간 동안 누른 상태 유지"""
    win32api.keybd_event(vk, 0, 0, 0)
    time.sleep(duration)
    win32api.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)


def apply_thrust(direction: str, duration: float = 1.0) -> dict:
    """
    지정 방향으로 추력 적용.

    Args:
        direction: forward, backward, left, right, up, down
        duration: 추력 적용 시간 (초)
    """
    vk = THRUST_KEY_MAP.get(direction)
    if vk is None:
        return {"status": "error", "message": f"알 수 없는 방향: {direction}"}

    try:
        _ensure_foreground()
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    _key_hold(vk, duration)
    return {"status": "ok", "direction": direction, "duration": duration}


def apply_rotation(axis: str, duration: float = 0.5) -> dict:
    """
    지정 축으로 회전 적용.

    Args:
        axis: yaw_left, yaw_right, pitch_up, pitch_down, roll_left, roll_right
        duration: 회전 적용 시간 (초)
    """
    vk = ROTATION_KEY_MAP.get(axis)
    if vk is None:
        return {"status": "error", "message": f"알 수 없는 회전축: {axis}"}

    try:
        _ensure_foreground()
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    _key_hold(vk, duration)
    return {"status": "ok", "axis": axis, "duration": duration}


def adjust_throttle(direction: str, taps: int = 5) -> dict:
    """
    스로틀 증감.

    Args:
        direction: "increase" (+키) 또는 "decrease" (-키)
        taps: 키 탭 횟수
    """
    vk = THROTTLE_KEYS.get(direction)
    if vk is None:
        return {"status": "error", "message": f"알 수 없는 방향: {direction}"}

    try:
        _ensure_foreground()
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    from spaceengine_mcp.bridges.console_bridge import _keybd_tap
    for _ in range(taps):
        _keybd_tap(vk, delay=0.05)
        time.sleep(0.1)

    return {"status": "ok", "direction": direction, "taps": taps}
