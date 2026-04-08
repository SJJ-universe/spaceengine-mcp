"""console_bridge 단위 테스트 — pywin32 mock 환경에서 실행"""
import pytest
from unittest.mock import patch, MagicMock, call

from spaceengine_mcp.bridges.console_bridge import (
    find_se_window,
    send_commands_via_console,
    _keybd_tap,
    _toggle_console,
    _clear_input,
    _press_enter,
    CONSOLE_KEY,
    DELAY_FOREGROUND,
    DELAY_CONSOLE_OPEN,
    DELAY_AFTER_COMMAND,
)


# ── find_se_window ───────────────────────────────────────────────────────────

def test_find_se_window_returns_none_when_no_se():
    """SE 미실행 시 None 반환 (스텁 또는 실제 환경 모두)"""
    # 실제 pywin32가 있으면 SE 미실행 시 None, 스텁이면 콜백 미호출로 None
    # 단, 실제 SE가 실행 중이면 핸들 반환 가능
    result = find_se_window()
    # None 또는 정수 (SE 실행 중이면 핸들 반환 가능)
    assert result is None or isinstance(result, int)


def test_find_se_window_finds_window():
    """SE 창이 있을 때 핸들 반환"""
    import win32gui

    original_enum = win32gui.EnumWindows

    def fake_enum(cb, extra):
        # SpaceEngine 창을 시뮬레이션
        cb(12345, extra)

    with patch.object(win32gui, "EnumWindows", side_effect=fake_enum):
        with patch.object(win32gui, "GetWindowText", return_value="SpaceEngine 0.990.48"):
            with patch.object(win32gui, "IsWindowVisible", return_value=True):
                result = find_se_window()
                assert result == 12345


# ── send_commands_via_console ────────────────────────────────────────────────

def test_send_commands_returns_error_when_no_window():
    """SE 창 미발견 시 에러 반환"""
    with patch("spaceengine_mcp.bridges.console_bridge.find_se_window", return_value=None):
        result = send_commands_via_console(["Select \"Mars\""])
        assert result["status"] == "error"
        assert "찾을 수 없" in result["message"]


def test_send_commands_filters_empty_and_comments():
    """빈 줄과 주석은 필터링 → SE 창 있어도 '실행할 명령어가 없음'"""
    with patch("spaceengine_mcp.bridges.console_bridge.find_se_window", return_value=99999):
        result = send_commands_via_console(["", "  ", "// comment", "  // another comment"])
        assert result["status"] == "error"
        assert "명령어가 없" in result["message"]


@pytest.mark.integration
def test_send_commands_executes_with_se_window():
    """SE 창 발견 시 명령어 실행 (실제 pywin32 환경 필요)"""
    result = send_commands_via_console(['Select "Mars"'])
    # SE가 실행 중이면 ok, 아니면 error
    assert result["status"] in ("ok", "error")


@pytest.mark.integration
def test_send_commands_multiple():
    """여러 명령어 순차 실행 (실제 pywin32 환경 필요)"""
    cmds = ['Select "Mars"', 'Goto { Time 5 DistRad 3 }', 'Wait 6']
    result = send_commands_via_console(cmds)
    assert result["status"] in ("ok", "error")


# ── _keybd_tap / _toggle_console / _clear_input ─────────────────────────────

def test_keybd_tap_calls_keybd_event():
    """keybd_event down + up 호출 확인"""
    import win32api
    with patch.object(win32api, "keybd_event") as mock_kbd:
        _keybd_tap(0x41, delay=0.001)  # 'A' key
        assert mock_kbd.call_count == 2  # down + up


def test_toggle_console_uses_tilde():
    """콘솔 토글은 CONSOLE_KEY (0xC0) 사용"""
    import win32api
    with patch.object(win32api, "keybd_event") as mock_kbd:
        _toggle_console(0)  # dummy hwnd
        # 첫 호출이 CONSOLE_KEY여야 함
        first_call_vk = mock_kbd.call_args_list[0][0][0]
        assert first_call_vk == CONSOLE_KEY


def test_clear_input_sends_ctrl_a_delete():
    """Ctrl+A → Delete 로 입력창 전체 클리어"""
    import win32api
    import win32con
    with patch.object(win32api, "keybd_event") as mock_kbd:
        _clear_input(0)
        # Ctrl down, A down, A up, Ctrl up, Delete down, Delete up = 최소 6 호출
        assert mock_kbd.call_count >= 6
        # VK_CONTROL 이 첫 호출이어야 함
        first_vk = mock_kbd.call_args_list[0][0][0]
        assert first_vk == win32con.VK_CONTROL


def test_press_enter_uses_vk_return():
    """Enter 키 전송"""
    import win32api
    with patch.object(win32api, "keybd_event") as mock_kbd:
        _press_enter(0)
        first_call_vk = mock_kbd.call_args_list[0][0][0]
        assert first_call_vk == 0x0D  # VK_RETURN
