"""
테스트 전역 설정 — pywin32 스텁 + pytest 마커

pywin32가 없는 환경(CI/Linux)에서도 모든 bridge 모듈을
import하고 단위 테스트할 수 있도록 스텁 모듈을 제공합니다.
"""
import sys
import types

# ── pywin32가 없을 때만 스텁 주입 ────────────────────────────────────────────

def _ensure_pywin32_stubs():
    """win32api/win32gui/win32con/win32clipboard 스텁을 sys.modules에 삽입"""
    if "win32api" in sys.modules:
        return  # 이미 실제 모듈이 로드됨

    try:
        import win32api  # noqa: F401
        return  # 실제 설치됨
    except ImportError:
        pass

    # ── win32con 스텁 (VK_* 상수) ──────────────────────────────────────────
    win32con = types.ModuleType("win32con")
    # Virtual Key Codes
    win32con.VK_BACK = 0x08
    win32con.VK_TAB = 0x09
    win32con.VK_RETURN = 0x0D
    win32con.VK_SHIFT = 0x10
    win32con.VK_CONTROL = 0x11
    win32con.VK_MENU = 0x12  # Alt
    win32con.VK_SPACE = 0x20
    win32con.VK_PRIOR = 0x21  # Page Up
    win32con.VK_NEXT = 0x22   # Page Down
    win32con.VK_END = 0x23
    win32con.VK_HOME = 0x24
    win32con.VK_LEFT = 0x25
    win32con.VK_UP = 0x26
    win32con.VK_RIGHT = 0x27
    win32con.VK_DOWN = 0x28
    win32con.VK_INSERT = 0x2D
    win32con.VK_DELETE = 0x2E
    # F1~F12
    for i in range(1, 13):
        setattr(win32con, f"VK_F{i}", 0x6F + i)  # VK_F1=0x70
    # Window messages
    win32con.WM_CHAR = 0x0102
    win32con.CF_UNICODETEXT = 13
    win32con.SW_RESTORE = 9

    # ── win32api 스텁 ──────────────────────────────────────────────────────
    win32api = types.ModuleType("win32api")
    win32api.keybd_event = lambda *args, **kwargs: None
    win32api.SendMessage = lambda *args, **kwargs: 0

    # ── win32gui 스텁 ──────────────────────────────────────────────────────
    win32gui = types.ModuleType("win32gui")
    win32gui.EnumWindows = lambda cb, extra: None  # 콜백 호출 안함 → 창 미발견
    win32gui.GetWindowText = lambda hwnd: ""
    win32gui.IsWindowVisible = lambda hwnd: False
    win32gui.ShowWindow = lambda hwnd, cmd: None
    win32gui.SetForegroundWindow = lambda hwnd: None
    win32gui.GetWindowRect = lambda hwnd: (0, 0, 1920, 1080)

    # ── win32clipboard 스텁 ────────────────────────────────────────────────
    win32clipboard = types.ModuleType("win32clipboard")
    win32clipboard.OpenClipboard = lambda *args: None
    win32clipboard.EmptyClipboard = lambda: None
    win32clipboard.SetClipboardData = lambda fmt, data: None
    win32clipboard.CloseClipboard = lambda: None

    # sys.modules에 등록
    sys.modules["win32con"] = win32con
    sys.modules["win32api"] = win32api
    sys.modules["win32gui"] = win32gui
    sys.modules["win32clipboard"] = win32clipboard


# conftest.py 로드 시점에 즉시 실행 (모든 테스트 수집 전)
_ensure_pywin32_stubs()
