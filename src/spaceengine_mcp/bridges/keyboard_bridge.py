"""
SpaceEngine 키보드 브릿지 — 콘솔 외 키보드 입력 자동화.

콘솔을 열지 않고 SE 게임 창에 직접 키 입력을 전송합니다.
F3(검색), F9(녹화), 1/2/3(모드 전환) 등 콘솔로 불가능한 기능을 커버합니다.

핵심 원칙:
- ESC 키 차단 (SE에서 ESC = 메인메뉴 이동)
- 모든 키 입력 = keybd_event (DirectInput 호환)
- SE 포어그라운드 필수
"""
import logging
import time

import win32api
import win32con
import win32gui

from spaceengine_mcp.bridges.console_bridge import (
    find_se_window,
    _keybd_tap,
    _paste_via_clipboard,
    KEYEVENTF_KEYUP,
    DELAY_FOREGROUND,
)

logger = logging.getLogger(__name__)

# ── 키 이름 → VK 코드 매핑 ──────────────────────────────────────────────────
KEY_NAME_MAP: dict[str, int] = {
    # 함수 키
    "f1": win32con.VK_F1, "f2": win32con.VK_F2, "f3": win32con.VK_F3,
    "f4": win32con.VK_F4, "f5": win32con.VK_F5, "f6": win32con.VK_F6,
    "f7": win32con.VK_F7, "f8": win32con.VK_F8, "f9": win32con.VK_F9,
    "f10": win32con.VK_F10, "f11": win32con.VK_F11, "f12": win32con.VK_F12,
    # 숫자
    "0": ord('0'), "1": ord('1'), "2": ord('2'), "3": ord('3'),
    "4": ord('4'), "5": ord('5'), "6": ord('6'), "7": ord('7'),
    "8": ord('8'), "9": ord('9'),
    # 알파벳
    "a": ord('A'), "b": ord('B'), "c": ord('C'), "d": ord('D'),
    "e": ord('E'), "f": ord('F'), "g": ord('G'), "h": ord('H'),
    "i": ord('I'), "j": ord('J'), "k": ord('K'), "l": ord('L'),
    "m": ord('M'), "n": ord('N'), "o": ord('O'), "p": ord('P'),
    "q": ord('Q'), "r": ord('R'), "s": ord('S'), "t": ord('T'),
    "u": ord('U'), "v": ord('V'), "w": ord('W'), "x": ord('X'),
    "y": ord('Y'), "z": ord('Z'),
    # 특수
    "space": win32con.VK_SPACE, "enter": win32con.VK_RETURN,
    "tab": win32con.VK_TAB, "backspace": win32con.VK_BACK,
    "delete": win32con.VK_DELETE, "insert": win32con.VK_INSERT,
    "home": win32con.VK_HOME, "end": win32con.VK_END,
    "pageup": win32con.VK_PRIOR, "pagedown": win32con.VK_NEXT,
    "up": win32con.VK_UP, "down": win32con.VK_DOWN,
    "left": win32con.VK_LEFT, "right": win32con.VK_RIGHT,
    "plus": 0xBB, "minus": 0xBD,  # VK_OEM_PLUS / VK_OEM_MINUS
    # ESC는 의도적으로 생략 — 차단됨
}

MODIFIER_MAP: dict[str, int] = {
    "ctrl": win32con.VK_CONTROL,
    "shift": win32con.VK_SHIFT,
    "alt": win32con.VK_MENU,
}

BLOCKED_KEYS = {"escape", "esc"}


def _ensure_foreground() -> int:
    """SE 창을 찾아 포어그라운드로 설정. 핸들 반환."""
    hwnd = find_se_window()
    if hwnd is None:
        raise RuntimeError("실행 중인 SpaceEngine 창을 찾을 수 없음")
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(DELAY_FOREGROUND)
    return hwnd


def send_key(key_name: str, modifiers: list[str] | None = None) -> dict:
    """
    SE 게임 창에 단일 키를 전송합니다 (콘솔 미사용).

    Args:
        key_name: 키 이름 (소문자, 예: "f3", "1", "a")
        modifiers: 수정자 키 리스트 (예: ["ctrl"], ["ctrl", "shift"])
    """
    key_lower = key_name.lower()
    if key_lower in BLOCKED_KEYS:
        return {"status": "error", "message": "ESC 키는 SE 안전을 위해 차단됩니다."}

    vk = KEY_NAME_MAP.get(key_lower)
    if vk is None:
        return {"status": "error", "message": f"알 수 없는 키: {key_name}"}

    try:
        _ensure_foreground()
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    # 수정자 키 누르기
    mod_vks = []
    if modifiers:
        for mod_name in modifiers:
            mod_vk = MODIFIER_MAP.get(mod_name.lower())
            if mod_vk is None:
                return {"status": "error", "message": f"알 수 없는 수정자 키: {mod_name}"}
            mod_vks.append(mod_vk)
            win32api.keybd_event(mod_vk, 0, 0, 0)
        time.sleep(0.05)

    # 메인 키 누르기
    _keybd_tap(vk, delay=0.05)

    # 수정자 키 해제 (역순)
    for mod_vk in reversed(mod_vks):
        win32api.keybd_event(mod_vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)

    return {"status": "ok", "key": key_name, "modifiers": modifiers or []}


def send_key_then_type(pre_key: str, text: str, delay_after_key: float = 0.8) -> dict:
    """
    키를 눌러 다이얼로그를 열고, 텍스트를 입력 후 Enter를 누릅니다.
    예: F3 → 검색어 입력 → Enter

    Args:
        pre_key: 다이얼로그를 여는 키 (예: "f3")
        text: 입력할 텍스트
        delay_after_key: 다이얼로그 열림 대기 시간 (초)
    """
    key_lower = pre_key.lower()
    if key_lower in BLOCKED_KEYS:
        return {"status": "error", "message": "ESC 키는 차단됩니다."}

    vk = KEY_NAME_MAP.get(key_lower)
    if vk is None:
        return {"status": "error", "message": f"알 수 없는 키: {pre_key}"}

    try:
        _ensure_foreground()
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    # 키로 다이얼로그 열기
    _keybd_tap(vk, delay=0.05)
    time.sleep(delay_after_key)

    # 텍스트 입력 (클립보드+Ctrl+V)
    try:
        _paste_via_clipboard(text)
    except Exception as e:
        return {"status": "error", "message": f"텍스트 입력 실패: {e}"}

    # Enter
    time.sleep(0.1)
    _keybd_tap(win32con.VK_RETURN, delay=0.05)
    time.sleep(0.3)

    return {"status": "ok", "key": pre_key, "text": text}
