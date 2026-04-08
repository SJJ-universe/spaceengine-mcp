"""Phase 10 — FlightBridge 단위 테스트

실제 키 전송은 SE 실행 필요 → 키 매핑 로직만 검증
"""

from spaceengine_mcp.bridges.flight_bridge import (
    THRUST_KEY_MAP,
    ROTATION_KEY_MAP,
    THROTTLE_KEYS,
)


# ── THRUST_KEY_MAP ───────────────────────────────────────────────────────────

def test_thrust_map_has_all_directions():
    expected = {"forward", "backward", "left", "right", "up", "down"}
    assert set(THRUST_KEY_MAP.keys()) == expected


def test_thrust_map_values_are_ints():
    for key, vk in THRUST_KEY_MAP.items():
        assert isinstance(vk, int), f"Thrust '{key}' has non-int VK: {vk}"


# ── ROTATION_KEY_MAP ─────────────────────────────────────────────────────────

def test_rotation_map_has_all_axes():
    expected = {"yaw_left", "yaw_right", "pitch_up", "pitch_down", "roll_left", "roll_right"}
    assert set(ROTATION_KEY_MAP.keys()) == expected


def test_rotation_map_values_are_ints():
    for key, vk in ROTATION_KEY_MAP.items():
        assert isinstance(vk, int), f"Rotation '{key}' has non-int VK: {vk}"


# ── THROTTLE_KEYS ────────────────────────────────────────────────────────────

def test_throttle_keys():
    assert "increase" in THROTTLE_KEYS
    assert "decrease" in THROTTLE_KEYS
    assert isinstance(THROTTLE_KEYS["increase"], int)
    assert isinstance(THROTTLE_KEYS["decrease"], int)
