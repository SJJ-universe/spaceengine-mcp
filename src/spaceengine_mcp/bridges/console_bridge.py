"""
SpaceEngine 인게임 콘솔 브릿지.

핵심 원칙:
- ESC 키는 절대 사용 금지 (SE에서 ESC = 메인 화면으로 이동)
- 콘솔 열기/닫기는 반드시 ` (tilde, 0xC0) 키만 사용
- 텍스트 입력: 클립보드 + keybd_event Ctrl+V (SE 포어그라운드 상태에서 동작)
- 모든 키 입력: keybd_event 사용 (SE는 DirectInput — WM_KEYDOWN 불신뢰)
- 클립보드 실패 시 WM_CHAR 폴백
- 포커스 전환에 keybd_event는 절대 사용 금지 (다른 앱에 키 전달됨)
"""
import ctypes
import logging
import time
import win32api
import win32clipboard
import win32gui
import win32con

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

logger = logging.getLogger(__name__)

CONSOLE_KEY = 0xC0   # ` / ~ 키 (tilde) — SE 콘솔 토글
KEYEVENTF_KEYUP = 0x0002

# ── 타이밍 설정 (초) ──────────────────────────────────────────────────────────
DELAY_FOREGROUND = 0.7       # SetForegroundWindow 후 대기
DELAY_CONSOLE_OPEN = 1.0     # 콘솔 열기 후 대기
DELAY_AFTER_COMMAND = 0.5    # 기본 명령어 실행 후 대기
DELAY_AFTER_COMMAND_HEAVY = 0.6  # 무거운 명령어
DELAY_CLIPBOARD_BEFORE = 0.25
DELAY_CLIPBOARD_AFTER = 0.25
DELAY_BEFORE_ENTER = 0.2

_HEAVY_CMD_PREFIXES = ("Goto", "Run", "SplinePath", "Wait", "Center", "Land", "SetFOV")


def find_se_window() -> int | None:
    """실행 중인 SpaceEngine 게임 창 핸들 반환.

    ★ 중요: Electron 앱("SpaceEngine MCP")을 SE 게임 창으로 잘못 인식하면
    키 입력이 Electron에 전달되어 명령이 SE에 도달하지 않는다.
    반드시 'MCP'가 포함된 창, 'Electron' 창 등을 제외해야 한다.
    """
    result = []

    def _cb(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if not win32gui.IsWindowVisible(hwnd):
            return True
        # "SpaceEngine"이 포함되어야 하지만
        # "MCP", "Electron", "DevTools" 등은 제외 (Electron 앱 구분)
        if "SpaceEngine" in title and "MCP" not in title and "Electron" not in title and "DevTools" not in title:
            result.append(hwnd)
            logger.debug(f"SE 게임 창 발견: hwnd={hwnd}, title='{title}'")
        return True

    win32gui.EnumWindows(_cb, None)
    if not result:
        logger.warning("SpaceEngine 게임 창을 찾을 수 없음 — SE가 실행 중인지 확인하세요")
    return result[0] if result else None


def _is_se_foreground(hwnd: int) -> bool:
    """SE 창이 현재 포어그라운드(활성 창)인지 확인."""
    return _user32.GetForegroundWindow() == hwnd


def _is_se_foreground_stable(hwnd: int, checks: int = 3, interval: float = 0.15) -> bool:
    """SE가 안정적으로 포어그라운드를 유지하는지 확인 (깜빡임 방지)."""
    for _ in range(checks):
        if not _is_se_foreground(hwnd):
            return False
        time.sleep(interval)
    return True


def _force_foreground(hwnd: int) -> bool:
    """
    SE 창을 강제로 포어그라운드로 전환. 성공 시 True.

    ★ keybd_event는 절대 사용 금지! ★
    keybd_event는 "현재 포어그라운드 창"에 키를 보내므로
    Electron 등 다른 앱이 활성 상태면 그 앱에 Alt/키가 전달되어
    앱이 종료되거나 의도치 않은 동작이 발생한다.
    """
    if _is_se_foreground(hwnd):
        return True

    logger.info(f"SE 포커스 전환 시작 (hwnd={hwnd})")

    # ── 방법 1: COM AppActivate (백그라운드에서 가장 신뢰성 높음) ──
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            activated = shell.AppActivate("SpaceEngine")
            logger.debug(f"AppActivate 반환값: {activated}")
            time.sleep(0.5)
            if _is_se_foreground_stable(hwnd):
                logger.info("포커스 전환 성공 (AppActivate)")
                return True
        finally:
            pythoncom.CoUninitialize()
    except Exception as e:
        logger.warning(f"AppActivate 실패: {e}")

    # ── 방법 2: HWND_TOPMOST + AttachThreadInput ──
    # SetWindowPos(TOPMOST)는 포어그라운드 권한 없이도 창을 최상위로 올릴 수 있음
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.1)

        # 최상위로 올리기 (포어그라운드 권한 불필요)
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )
        time.sleep(0.1)

        # AttachThreadInput으로 포어그라운드 스레드의 입력 큐에 연결
        fg_hwnd = _user32.GetForegroundWindow()
        curr_tid = _kernel32.GetCurrentThreadId()
        fg_tid = _user32.GetWindowThreadProcessId(fg_hwnd, None)

        attached = False
        if fg_tid and fg_tid != curr_tid:
            attached = bool(_user32.AttachThreadInput(curr_tid, fg_tid, True))

        _user32.BringWindowToTop(hwnd)
        _user32.SetForegroundWindow(hwnd)

        if attached:
            _user32.AttachThreadInput(curr_tid, fg_tid, False)

        # TOPMOST 해제 (SE가 항상 최상위에 고정되지 않도록)
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )
        time.sleep(0.5)

        if _is_se_foreground_stable(hwnd):
            logger.info("포커스 전환 성공 (TOPMOST+Attach)")
            return True
    except Exception as e:
        logger.warning(f"TOPMOST+Attach 실패: {e}")

    # ── 방법 3: Minimize → Restore (z-order 강제 리셋) ──
    try:
        logger.warning("포커스 전환 재시도 — Minimize+Restore")
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        time.sleep(0.4)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.6)
        _user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)

        if _is_se_foreground_stable(hwnd):
            logger.info("포커스 전환 성공 (Minimize+Restore)")
            return True
    except Exception as e:
        logger.warning(f"Minimize+Restore 실패: {e}")

    # ── 방법 4: ForegroundLockTimeout 해제 ──
    try:
        SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
        SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001

        old_timeout = ctypes.c_uint(0)
        _user32.SystemParametersInfoW(
            SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(old_timeout), 0,
        )
        # timeout을 0으로 설정 (포어그라운드 잠금 해제)
        _user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, None, 0)

        _user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)

        # 원래 값 복원
        _user32.SystemParametersInfoW(
            SPI_SETFOREGROUNDLOCKTIMEOUT, 0,
            ctypes.cast(old_timeout.value, ctypes.c_void_p), 0,
        )

        if _is_se_foreground_stable(hwnd):
            logger.info("포커스 전환 성공 (ForegroundLockTimeout)")
            return True
    except Exception as e:
        logger.warning(f"ForegroundLockTimeout 실패: {e}")

    logger.error("SE 창 포커스 전환 실패 — 모든 방법(4가지) 시도 완료")
    return False


# ── 저수준 키/텍스트 전송 헬퍼 ─────────────────────────────────────────────

def _keybd_tap(vk: int, delay: float = 0.05):
    """keybd_event로 키 누름+뗌 전송 (DirectInput 호환, 포어그라운드 창으로 전달)."""
    win32api.keybd_event(vk, 0, 0, 0)
    time.sleep(delay)
    win32api.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(delay)


def _toggle_console(_hwnd: int):
    """` 키로 SE 콘솔 토글 (열기 또는 닫기) — keybd_event 사용."""
    _keybd_tap(CONSOLE_KEY, delay=0.05)
    time.sleep(0.3)


def _clear_input(_hwnd: int):
    """Ctrl+A → Delete 로 입력창 전체 선택 후 삭제 (Backspace 반복보다 확실)."""
    # Ctrl+A: 전체 선택
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('A'), 0, 0, 0)
    time.sleep(0.03)
    win32api.keybd_event(ord('A'), 0, KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    # Delete: 선택 영역 삭제
    win32api.keybd_event(win32con.VK_DELETE, 0, 0, 0)
    win32api.keybd_event(win32con.VK_DELETE, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)


def _paste_via_clipboard(text: str):
    """
    클립보드에 텍스트 설정 후 keybd_event Ctrl+V 전송.
    SE가 포어그라운드(활성 창)이어야 동작함.
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            win32clipboard.CloseClipboard()
            break
        except Exception as e:
            if attempt < max_attempts - 1:
                logger.warning(f"클립보드 접근 실패 ({attempt+1}/{max_attempts}), 재시도: {e}")
                time.sleep(0.3)
            else:
                raise  # 최종 실패 → WM_CHAR 폴백으로 전파

    # 클립보드 쓰기 완료 후 충분한 대기 (이전 Ctrl+V와의 간섭 방지)
    time.sleep(DELAY_CLIPBOARD_BEFORE)

    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    time.sleep(0.03)
    win32api.keybd_event(ord('V'), 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(ord('V'), 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.03)
    win32api.keybd_event(win32con.VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(DELAY_CLIPBOARD_AFTER)


def _type_via_wm_char(hwnd: int, text: str, delay: float = 0.025):
    """WM_CHAR 폴백: 한 글자씩 직접 전송. ASCII 전용 명령어에서만 신뢰 가능."""
    for ch in text:
        win32api.SendMessage(hwnd, win32con.WM_CHAR, ord(ch), 0)
        time.sleep(delay)


def _press_enter(hwnd: int):
    """keybd_event로 Enter 전송 — DirectInput 호환."""
    _keybd_tap(win32con.VK_RETURN, delay=0.05)


# ── 공개 API ─────────────────────────────────────────────────────────────────

# 배치 내 중복 허용 명령어 접두사 (Wait, Print는 의도적 반복 가능)
_REPEATABLE_CMD_PREFIXES = ("Wait", "Print", "HidePrint")


def _send_batch(hwnd: int, cmds: list[str], close_console: bool = True) -> list[str]:
    """콘솔 세션 하나에서 명령어 리스트 실행 (내부 헬퍼)."""
    # 콘솔 상태 불명 → 먼저 닫기(이미 열려있으면 닫힘, 이미 닫혀있으면 열렸다가 바로 닫힘)
    # 그 다음 다시 열기 → 항상 열린 상태로 시작 보장
    _toggle_console(hwnd)
    time.sleep(0.3)
    _toggle_console(hwnd)
    time.sleep(DELAY_CONSOLE_OPEN)

    executed = []
    seen = set()  # 배치 전체 중복 추적
    for cmd in cmds:
        # 매 명령 전 SE가 여전히 포어그라운드인지 확인
        if not _is_se_foreground(hwnd):
            logger.warning("명령 실행 중 SE 포커스 이탈 감지 — 재확보 시도")
            if not _force_foreground(hwnd):
                logger.error("포커스 재확보 실패 — 나머지 명령 중단")
                break
            # 포커스 복구 후 콘솔 다시 열기
            _toggle_console(hwnd)
            time.sleep(0.3)
            _toggle_console(hwnd)
            time.sleep(DELAY_CONSOLE_OPEN)

        first_word = cmd.split()[0] if cmd.split() else ""
        is_repeatable = first_word in _REPEATABLE_CMD_PREFIXES

        # 반복 불가 명령: 배치 내에서 이미 실행했으면 스킵
        if not is_repeatable and cmd in seen:
            logger.debug(f"배치 내 중복 명령 스킵: {cmd}")
            continue

        seen.add(cmd)
        _clear_input(hwnd)
        try:
            _paste_via_clipboard(cmd)
        except Exception as e:
            logger.warning(f"클립보드 실패, WM_CHAR 폴백 사용: {e}")
            _type_via_wm_char(hwnd, cmd)
        time.sleep(DELAY_BEFORE_ENTER)
        _press_enter(hwnd)
        executed.append(cmd)
        # 명령 타입에 따른 적응적 딜레이
        delay = DELAY_AFTER_COMMAND_HEAVY if first_word in _HEAVY_CMD_PREFIXES else DELAY_AFTER_COMMAND
        time.sleep(delay)

    if close_console:
        _toggle_console(hwnd)
    return executed


def send_commands_via_console(commands: list[str], close_console: bool = True) -> dict:
    """
    SE 인게임 콘솔에 명령어를 직접 입력하여 실행.

    모든 명령어를 단일 콘솔 세션에서 순차 전송.
    (SE 콘솔은 .se 파일의 모든 명령어를 직접 실행 가능)

    Args:
        commands: SE 명령어 리스트 (주석·빈줄 자동 제거)
        close_console: 실행 후 콘솔 닫기 여부
    """
    hwnd = find_se_window()
    if hwnd is None:
        return {"status": "error", "message": "실행 중인 SpaceEngine 창을 찾을 수 없음"}

    cmds = [c.strip() for c in commands if c.strip() and not c.strip().startswith("//")]
    if not cmds:
        return {"status": "error", "message": "실행할 명령어가 없음"}

    try:
        # SE 창을 포어그라운드로 가져오기
        if not _force_foreground(hwnd):
            return {
                "status": "error",
                "message": "SpaceEngine 창으로 포커스 전환 실패 — SE가 실행 중이고 최소화되지 않았는지 확인하세요",
            }

        # 최종 확인: 키 입력 직전에 SE가 확실히 포어그라운드인지 한 번 더 체크
        if not _is_se_foreground(hwnd):
            return {
                "status": "error",
                "message": "SE 포커스 전환 직후 포커스가 다시 이탈됨 — 다른 앱이 포커스를 가져갔을 수 있습니다",
            }

        executed = _send_batch(hwnd, cmds, close_console=close_console)

        # 부분 실행 감지: 요청한 명령 수와 실행된 명령 수 비교
        if len(executed) == 0:
            return {
                "status": "error",
                "message": "명령어가 하나도 실행되지 않음 — SE 포커스를 유지할 수 없었습니다",
            }
        if len(executed) < len(cmds):
            return {
                "status": "partial",
                "message": f"{len(cmds)}개 중 {len(executed)}개만 실행됨 — 중간에 포커스 이탈 발생",
                "executed": executed,
                "count": len(executed),
                "total_requested": len(cmds),
            }

        return {"status": "ok", "executed": executed, "count": len(executed)}

    except Exception as e:
        logger.error(f"콘솔 명령 실행 오류: {e}")
        return {"status": "error", "message": str(e)}
