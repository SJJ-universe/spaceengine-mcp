"""Phase 7 — KeyboardBridge 단위 테스트

실제 키 전송은 SE 실행 필요 → 키 매핑/차단 로직만 검증
"""
import pytest

from spaceengine_mcp.bridges.keyboard_bridge import (
    KEY_NAME_MAP,
    MODIFIER_MAP,
    BLOCKED_KEYS,
)


# ── KEY_NAME_MAP ─────────────────────────────────────────────────────────────

def test_key_name_map_has_function_keys():
    """F1~F12 키가 모두 매핑됨"""
    for i in range(1, 13):
        assert f"f{i}" in KEY_NAME_MAP


def test_key_name_map_has_digits():
    """0~9 숫자 키 매핑"""
    for d in "0123456789":
        assert d in KEY_NAME_MAP


def test_key_name_map_has_alphabet():
    """a~z 알파벳 키 매핑"""
    for ch in "abcdefghijklmnopqrstuvwxyz":
        assert ch in KEY_NAME_MAP


def test_key_name_map_values_are_ints():
    """모든 VK 코드가 정수"""
    for key, vk in KEY_NAME_MAP.items():
        assert isinstance(vk, int), f"Key '{key}' has non-int VK: {vk}"


# ── MODIFIER_MAP ─────────────────────────────────────────────────────────────

def test_modifier_map_has_ctrl_shift_alt():
    assert "ctrl" in MODIFIER_MAP
    assert "shift" in MODIFIER_MAP
    assert "alt" in MODIFIER_MAP


# ── BLOCKED_KEYS ─────────────────────────────────────────────────────────────

def test_esc_is_blocked():
    """ESC 키가 차단 목록에 포함"""
    assert "escape" in BLOCKED_KEYS
    assert "esc" in BLOCKED_KEYS


def test_esc_not_in_key_map():
    """ESC가 KEY_NAME_MAP에 없음 (이중 안전)"""
    assert "escape" not in KEY_NAME_MAP
    assert "esc" not in KEY_NAME_MAP
