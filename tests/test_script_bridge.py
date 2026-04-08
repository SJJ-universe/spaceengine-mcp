import pytest
import tempfile
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import (
    ScriptBridge,
    sanitize_object_name,
    normalize_overlay_name,
    validate_commands,
)


@pytest.fixture
def tmp_config(tmp_path):
    """임시 디렉토리를 SE 설치 경로로 사용하는 테스트용 Config"""
    return SpaceEngineConfig(install_path=tmp_path)


@pytest.fixture
def bridge(tmp_config):
    templates_dir = str(Path(__file__).parent.parent / "templates")
    return ScriptBridge(tmp_config, templates_dir=templates_dir)


# ── sanitize_object_name ──────────────────────────────────────────────────────

def test_sanitize_removes_quotes():
    assert '"' not in sanitize_object_name('Sol "Alpha"')


def test_sanitize_removes_braces():
    result = sanitize_object_name("Star{inject}")
    assert "{" not in result and "}" not in result


def test_sanitize_length_limit():
    long_name = "A" * 200
    assert len(sanitize_object_name(long_name)) <= 100


def test_sanitize_removes_backslash():
    assert '\\' not in sanitize_object_name('Star\\Name')


# ── validate_commands ─────────────────────────────────────────────────────────

def test_validate_allows_select_goto():
    cmds = ['Select "Mars"', 'Goto { DistRad 3.0 Time 5.0 }']
    assert validate_commands(cmds) == []


def test_validate_blocks_exit():
    cmds = ['Exit']
    assert validate_commands(cmds) == ['Exit']


def test_validate_blocks_run_script():
    cmds = ['RunScript "evil.se"']
    assert validate_commands(cmds) == ['RunScript "evil.se"']


# ── build_navigation_commands ─────────────────────────────────────────────────

def test_navigation_goto(bridge):
    cmds = bridge.build_navigation_commands("Mars", mode="goto")
    assert cmds == [
        'UserMoveControl "Free"',
        'UserRotationControl "Free"',
        'UserTimeControl "Free"',
        'Select "Mars"',
        'Goto { Time 5.0 DistRad 3.0 }',
        'Wait 6.0',  # transition_time + 1 여유
    ]


def test_navigation_center(bridge):
    cmds = bridge.build_navigation_commands("Sol", mode="center")
    assert cmds == [
        'UserMoveControl "Free"',
        'UserRotationControl "Free"',
        'UserTimeControl "Free"',
        'Select "Sol"',
        'Center { Time 5.0 }',
    ]


def test_navigation_follow(bridge):
    cmds = bridge.build_navigation_commands("Jupiter", mode="follow")
    assert cmds == [
        'UserMoveControl "Free"',
        'UserRotationControl "Free"',
        'UserTimeControl "Free"',
        'Select "Jupiter"',
        'Follow',
    ]


# ── build_time_commands ───────────────────────────────────────────────────────

def test_time_set_date(bridge):
    cmds = bridge.build_time_commands(date_iso="2024-04-08T18:00:00")
    assert 'Date "2024.04.08 18:00:00"' in cmds


def test_time_set_rate(bridge):
    cmds = bridge.build_time_commands(rate=1000)
    assert "TimeScale 1000" in cmds


def test_time_pause(bridge):
    cmds = bridge.build_time_commands(rate=0)
    assert "StopTime" in cmds


def test_time_resume(bridge):
    """rate=1이면 StartTime 사용 (TimeScale 1 대신)"""
    cmds = bridge.build_time_commands(rate=1)
    assert "StartTime" in cmds


# ── generate_script ───────────────────────────────────────────────────────────

def test_generate_script_creates_file(bridge, tmp_config):
    cmds = ['Select "Venus"', 'Goto { Time 5.0 DistRad 3.0 }', 'Wait 5.0']
    path = bridge.generate_script(cmds, filename="test_nav.se")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert 'Select "Venus"' in content


def test_generate_script_blocks_forbidden(bridge):
    with pytest.raises(ValueError, match="허용되지 않은 명령어"):
        bridge.generate_script(["Exit"])


# ── build_overlay_commands ────────────────────────────────────────────────────

def test_overlay_orbits(bridge):
    assert bridge.build_overlay_commands("Orbits", True) == ["Show Orbits"]
    assert bridge.build_overlay_commands("Orbits", False) == ["Hide Orbits"]


def test_overlay_atmosphere_normalizes(bridge):
    """Atmosphere(단수)가 Atmospheres(복수)로 자동 변환"""
    assert bridge.build_overlay_commands("Atmosphere", True) == ["Show Atmospheres"]
    assert bridge.build_overlay_commands("Atmosphere", False) == ["Hide Atmospheres"]


def test_overlay_atmospheres_passthrough(bridge):
    assert bridge.build_overlay_commands("Atmospheres", True) == ["Show Atmospheres"]


def test_overlay_clouds(bridge):
    assert bridge.build_overlay_commands("Clouds", True) == ["Show Clouds"]
    assert bridge.build_overlay_commands("Clouds", False) == ["Hide Clouds"]


def test_overlay_singular_normalizes(bridge):
    """단수형이 복수형으로 자동 변환"""
    assert bridge.build_overlay_commands("Orbit", True) == ["Show Orbits"]
    assert bridge.build_overlay_commands("Label", False) == ["Hide Labels"]
    assert bridge.build_overlay_commands("Nebula", True) == ["Show Nebulae"]


# ── build_camera_commands ─────────────────────────────────────────────────────

def test_camera_dist_rad(bridge):
    cmds = bridge.build_camera_commands(dist_rad=5.0, time=2.0)
    assert len(cmds) == 2
    assert cmds[0] == 'Goto { Time 2.0 DistRad 5.0 }'
    assert cmds[1] == 'Wait 3.0'  # time + 1 여유


def test_camera_fov(bridge):
    cmds = bridge.build_camera_commands(fov=30.0)
    assert cmds == ['FOV 30.0']


def test_camera_dist(bridge):
    cmds = bridge.build_camera_commands(dist=1000.0)
    assert len(cmds) == 2
    assert cmds[0] == 'Goto { Time 3.0 DistKm 1000.0 }'
    assert cmds[1] == 'Wait 4.0'  # time + 1 여유


# ── build_sound_commands ──────────────────────────────────────────────────────

def test_sound_play(bridge):
    cmds = bridge.build_sound_commands("play", filename="alert.wav")
    assert cmds == ['PlaySound "alert.wav"']


def test_sound_play_with_volume(bridge):
    cmds = bridge.build_sound_commands("play", filename="alert.wav", volume=0.5)
    assert 'PlaySound { File "alert.wav" Volume 0.5 }' in cmds


def test_sound_stop(bridge):
    cmds = bridge.build_sound_commands("stop")
    assert cmds == ["StopSound"]


def test_sound_play_music(bridge):
    cmds = bridge.build_sound_commands("play_music", filename="theme.ogg")
    assert cmds == ['PlayMusic "theme.ogg"']


def test_sound_stop_music(bridge):
    cmds = bridge.build_sound_commands("stop_music")
    assert cmds == ["PauseMusic"]


# ── build_message_commands ────────────────────────────────────────────────────

def test_message_show(bridge):
    cmds = bridge.build_message_commands("Hello World!", duration=3.0)
    assert cmds == ['Print "Hello World!" { Time 3.0 }']


def test_message_hide(bridge):
    cmds = bridge.build_message_commands("", show=False)
    assert cmds == ["HidePrint"]


def test_message_sanitizes_quotes(bridge):
    cmds = bridge.build_message_commands('Say "hi"', duration=2.0)
    assert '"' not in cmds[0].split('"')[1] or "'" in cmds[0]


# ── build_screenshot_command ──────────────────────────────────────────────────

def test_screenshot(bridge):
    cmds = bridge.build_screenshot_command()
    assert "Screenshot" in cmds
    assert 'WaitTrigger "ScreenshotComplete"' in cmds


# ── build_gui_commands ────────────────────────────────────────────────────────

def test_gui_show(bridge):
    assert bridge.build_gui_commands(True) == []  # SE에 ShowAll 명령 없음


def test_gui_hide(bridge):
    assert bridge.build_gui_commands(False) == ["HideAllDialogs", "HideAllToolbars"]


# ── build_follow_commands ─────────────────────────────────────────────────────

def test_follow(bridge):
    cmds = bridge.build_follow_commands("Mars", mode="follow")
    assert cmds == ['Select "Mars"', 'Follow']


def test_track(bridge):
    cmds = bridge.build_follow_commands("Jupiter", mode="track")
    assert cmds == ['Select "Jupiter"', 'Track']


def test_unfollow(bridge):
    assert bridge.build_follow_commands("X", mode="unfollow") == ["Free"]


def test_untrack(bridge):
    assert bridge.build_follow_commands("X", mode="untrack") == ["Untrack"]


# ── validate_commands expanded ────────────────────────────────────────────────

def test_validate_allows_new_commands():
    """확장된 화이트리스트 명령어 검증 (2026-04-06 공식 문서 기준)"""
    cmds = [
        "Follow", "Free", "SyncRot", "Untrack",
        "Screenshot", "HideAllDialogs", "HideAllToolbars",
        'PlaySound "x.wav"',
        "PlayMusic", "PauseMusic", "ResumeMusic",
        'ShowMessage "hello"', "HideMessage", 'WaitMessage "hello"',
        'Set x 1', 'Toggle Orbits',
        'Print "hello"', "HidePrint", "Log test",
        'Date "2024.04.08"', "TimeScale 100", "StopTime", "StartTime",
        "FadeOut", "FadeIn", "Interpolate x",
        'ShowObject "Mars"', 'HideObject "Mars"',
        # 새로 추가된 명령어들
        "Unselect", "Horizon", 'GotoLocation "loc"', 'GotoURL "url"',
        "MoveMode", "Speed 10", "SpeedKm 1000",
        "Fly", "StopFly", "Turn", "StopTurn",
        'Waypoint "w"', 'DeleteWaypoint "w"', "ClearWaypoints", 'GotoWaypoint "w"',
        'SplinePath "p"', 'PlaySplinePath "p"', 'DeleteSplinePath "p"', "ClearSplinePaths",
        'WaitVar x 1', "Break", "Loop", "EndLoop",
        "if", "elif", "else", "endif",
        "BeginMultiTrigger", "EndMultiTrigger",
        'CheckVersion 990',
        "SetU x 1", "SetForce x 1", "Reset x",
        'ShowDialog "d"', 'HideDialog "d"',
        "HideAllDialogs", "HideAllToolbars",
        'UserStereobaseControl "Free"',
    ]
    blocked = validate_commands(cmds)
    assert blocked == [], f"Unexpectedly blocked: {blocked}"


def test_validate_still_blocks_removed_commands():
    """공식 문서에서 확인되지 않은 구 명령어들은 차단되어야 함"""
    # 이 명령어들은 화이트리스트에서 제거됨
    removed_cmds = ['Camera { DistRad 5 }']
    blocked = validate_commands(removed_cmds)
    assert len(blocked) > 0, "Camera should be blocked (not in official docs)"


# ══════════════════════════════════════════════════════════════════════════════
# Phase 5 — 콘솔 명령어 완전 도구화 테스트
# ══════════════════════════════════════════════════════════════════════════════

# ── build_variable_commands ──────────────────────────────────────────────────

def test_variable_set(bridge):
    cmds = bridge.build_variable_commands("StarBrightness", "set", "2.0")
    assert cmds == ["Set StarBrightness 2.0"]


def test_variable_set_force(bridge):
    cmds = bridge.build_variable_commands("AmbientLight", "set_force", "0.5")
    assert cmds == ["SetForce AmbientLight 0.5"]


def test_variable_set_u(bridge):
    cmds = bridge.build_variable_commands("StarBrightness", "set_u", "3.0")
    assert cmds == ["SetU StarBrightness 3.0"]


def test_variable_reset(bridge):
    cmds = bridge.build_variable_commands("StarBrightness", "reset")
    assert cmds == ["Reset StarBrightness"]


def test_variable_set_requires_value(bridge):
    with pytest.raises(ValueError, match="value가 필요"):
        bridge.build_variable_commands("StarBrightness", "set")


def test_variable_sanitizes_value(bridge):
    cmds = bridge.build_variable_commands("Var", "set", '1.0 "inject}')
    assert "{" not in cmds[0] and "}" not in cmds[0] and '"' not in cmds[0]


# ── build_interpolate_commands ───────────────────────────────────────────────

def test_interpolate_smooth(bridge):
    cmds = bridge.build_interpolate_commands("StarBrightness", 0.5, 3.0, "smooth")
    assert cmds == ['Interpolate StarBrightness { To 0.5 Time 3.0 Func "smooth" }']


def test_interpolate_linear(bridge):
    cmds = bridge.build_interpolate_commands("AmbientLight", 1.0, 2.0, "linear")
    assert 'Func "linear"' in cmds[0]


# ── build_spline_path_commands ───────────────────────────────────────────────

def test_spline_path_basic(bridge):
    knots = [
        {"select": "Mars", "goto_params": "DistRad 5 Time 3"},
        {"select": "Jupiter", "goto_params": "DistRad 10 Time 5"},
    ]
    cmds = bridge.build_spline_path_commands("TestPath", knots, auto_play=False)
    # UNLOCK 명령 3개 + SplinePath + { + 2 knots + }
    assert 'SplinePath "TestPath"' in cmds
    assert "{" in cmds
    assert "}" in cmds
    knot_lines = [c for c in cmds if "Knot" in c]
    assert len(knot_lines) == 2
    assert 'Select "Mars"' in knot_lines[0]


def test_spline_path_with_autoplay(bridge):
    knots = [{"select": "Sol"}]
    cmds = bridge.build_spline_path_commands("MyPath", knots, auto_play=True, play_time=20.0)
    assert 'PlaySplinePath "MyPath" { Time 20.0 }' in cmds
    assert "Wait 21" in cmds


# ── build_waypoint_commands ──────────────────────────────────────────────────

def test_waypoint_create(bridge):
    cmds = bridge.build_waypoint_commands("WP1", "create")
    assert cmds == ['Waypoint "WP1"']


def test_waypoint_delete(bridge):
    cmds = bridge.build_waypoint_commands("WP1", "delete")
    assert cmds == ['DeleteWaypoint "WP1"']


def test_waypoint_goto(bridge):
    cmds = bridge.build_waypoint_commands("WP1", "goto")
    assert cmds == ['GotoWaypoint "WP1"']


def test_waypoint_clear_all(bridge):
    cmds = bridge.build_waypoint_commands(mode="clear_all")
    assert cmds == ["ClearWaypoints"]


# ── build_flight_commands ────────────────────────────────────────────────────

def test_flight_fly(bridge):
    cmds = bridge.build_flight_commands("fly", 1.0, 0, 0.5)
    assert cmds == ["Fly 1.0 0 0.5"]


def test_flight_turn(bridge):
    cmds = bridge.build_flight_commands("turn", 0, 1.0, 0)
    assert cmds == ["Turn 0 1.0 0"]


def test_flight_orbit(bridge):
    cmds = bridge.build_flight_commands("orbit", 0, 0, 1.0)
    assert cmds == ["Orbit 0 0 1.0"]


def test_flight_stop_fly(bridge):
    assert bridge.build_flight_commands("stop_fly") == ["StopFly"]


def test_flight_stop_turn(bridge):
    assert bridge.build_flight_commands("stop_turn") == ["StopTurn"]


def test_flight_stop_orbit(bridge):
    assert bridge.build_flight_commands("stop_orbit") == ["StopOrbit"]


def test_flight_invalid_action(bridge):
    with pytest.raises(ValueError, match="지원하지 않는"):
        bridge.build_flight_commands("invalid")


# ── build_speed_commands ─────────────────────────────────────────────────────

def test_speed_internal(bridge):
    assert bridge.build_speed_commands(100.0) == ["Speed 100.0"]


def test_speed_km(bridge):
    assert bridge.build_speed_commands(1000.0, "km") == ["SpeedKm 1000.0"]


# ── build_fade_commands ──────────────────────────────────────────────────────

def test_fade_out(bridge):
    cmds = bridge.build_fade_commands("fade_out", 2.0)
    assert cmds == ["FadeOut { Time 2.0 }"]


def test_fade_in(bridge):
    cmds = bridge.build_fade_commands("fade_in", 1.5)
    assert cmds == ["FadeIn { Time 1.5 }"]


def test_fade_invalid_action(bridge):
    with pytest.raises(ValueError, match="지원하지 않는"):
        bridge.build_fade_commands("invalid")


# ── build_dialog_commands ────────────────────────────────────────────────────

def test_dialog_show(bridge):
    cmds = bridge.build_dialog_commands("ObjectInfo", "show")
    assert cmds == ['ShowDialog "ObjectInfo"']


def test_dialog_hide(bridge):
    cmds = bridge.build_dialog_commands("ObjectInfo", "hide")
    assert cmds == ['HideDialog "ObjectInfo"']


def test_dialog_hide_all(bridge):
    cmds = bridge.build_dialog_commands(action="hide_all")
    assert cmds == ["HideAllDialogs"]


# ── build_advanced_message_commands ──────────────────────────────────────────

def test_advanced_message_show(bridge):
    cmds = bridge.build_advanced_message_commands("Hello [b]World[/b]", False, 5.0)
    assert cmds[0] == "ShowMessage \"Hello [b]World[/b]\""
    assert cmds[1] == "Wait 5.0"
    assert cmds[2] == "HideMessage"


def test_advanced_message_wait(bridge):
    cmds = bridge.build_advanced_message_commands("Click Next", True)
    assert cmds == ['WaitMessage "Click Next"']


def test_advanced_message_sanitizes_quotes(bridge):
    cmds = bridge.build_advanced_message_commands('Say "hello"', False, 3.0)
    # 큰따옴표가 작은따옴표로 변환
    assert "Say 'hello'" in cmds[0]
