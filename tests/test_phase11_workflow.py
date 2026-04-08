"""Phase 11 워크플로 도구 단위 테스트"""
import json
import pytest
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge
from spaceengine_mcp.tools.phase11_workflow import (
    CinematicStep,
    PRESETS,
    _build_step_commands,
    _extract_object_info_from_log,
)


@pytest.fixture
def tmp_config(tmp_path):
    return SpaceEngineConfig(install_path=tmp_path)


@pytest.fixture
def bridge(tmp_config):
    templates_dir = str(Path(__file__).parent.parent / "templates")
    return ScriptBridge(tmp_config, templates_dir=templates_dir)


# ── CinematicStep 모델 ──────────────────────────────────────────────────────

class TestCinematicStepModel:
    def test_navigate_step(self):
        step = CinematicStep(action="navigate", target="Mars", distance_rad=5.0)
        assert step.action == "navigate"
        assert step.target == "Mars"
        assert step.distance_rad == 5.0

    def test_message_step(self):
        step = CinematicStep(action="message", text="Hello", value=3.0)
        assert step.text == "Hello"
        assert step.value == 3.0

    def test_wait_step(self):
        step = CinematicStep(action="wait", value=10.0)
        assert step.action == "wait"

    def test_optional_fields_default_none(self):
        step = CinematicStep(action="fade_out")
        assert step.target is None
        assert step.text is None
        assert step.value is None


# ── _build_step_commands ─────────────────────────────────────────────────────

class TestBuildStepCommands:
    def test_navigate(self, bridge):
        step = CinematicStep(action="navigate", target="Mars", distance_rad=5.0, transition_time=3.0)
        cmds = _build_step_commands(bridge, step)
        assert any('Select "Mars"' in c for c in cmds)
        assert any("Goto" in c for c in cmds)
        # UNLOCK 명령은 제거되어야 함
        assert not any("UserMoveControl" in c for c in cmds)

    def test_fade_out(self, bridge):
        step = CinematicStep(action="fade_out", value=2.0)
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["FadeOut { Time 2.0 }"]

    def test_fade_in(self, bridge):
        step = CinematicStep(action="fade_in", value=1.5)
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["FadeIn { Time 1.5 }"]

    def test_message(self, bridge):
        step = CinematicStep(action="message", text="Welcome", value=5.0)
        cmds = _build_step_commands(bridge, step)
        assert any("Print" in c and "Welcome" in c for c in cmds)

    def test_wait(self, bridge):
        step = CinematicStep(action="wait", value=7.0)
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["Wait 7.0"]

    def test_follow(self, bridge):
        step = CinematicStep(action="follow", target="Earth")
        cmds = _build_step_commands(bridge, step)
        assert 'Select "Earth"' in cmds
        assert "Follow" in cmds

    def test_unfollow(self, bridge):
        step = CinematicStep(action="unfollow")
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["Free"]

    def test_hide_gui(self, bridge):
        step = CinematicStep(action="hide_gui")
        cmds = _build_step_commands(bridge, step)
        # GUI 명령은 콘솔 직접 전송, 스크립트에는 빈 리스트
        assert cmds == []

    def test_show_gui(self, bridge):
        step = CinematicStep(action="show_gui")
        cmds = _build_step_commands(bridge, step)
        # GUI 명령은 콘솔 직접 전송, 스크립트에는 빈 리스트
        assert cmds == []

    def test_set_fov(self, bridge):
        step = CinematicStep(action="set_fov", value=90.0)
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["FOV 90.0"]

    def test_overlay_on(self, bridge):
        step = CinematicStep(action="overlay_on", overlay="Labels")
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["Show Labels"]

    def test_overlay_off(self, bridge):
        step = CinematicStep(action="overlay_off", overlay="Orbits")
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["Hide Orbits"]

    def test_flyby(self, bridge):
        step = CinematicStep(action="flyby", target="Jupiter", distance_rad=15.0)
        cmds = _build_step_commands(bridge, step)
        assert 'Select "Jupiter"' in cmds
        assert any("Goto" in c for c in cmds)

    def test_screenshot(self, bridge):
        step = CinematicStep(action="screenshot")
        cmds = _build_step_commands(bridge, step)
        assert "Screenshot" in cmds

    def test_set_time(self, bridge):
        step = CinematicStep(action="set_time", date="2024-04-08T18:00:00")
        cmds = _build_step_commands(bridge, step)
        assert any("Date" in c and "2024.04.08" in c for c in cmds)

    def test_time_rate(self, bridge):
        step = CinematicStep(action="time_rate", value=1000.0)
        cmds = _build_step_commands(bridge, step)
        assert cmds == ["TimeScale 1000.0"]

    def test_defaults_when_missing(self, bridge):
        """value/target 생략 시 기본값 사용"""
        step = CinematicStep(action="navigate")  # target=None
        cmds = _build_step_commands(bridge, step)
        assert any('Select "Earth"' in c for c in cmds)  # default target


# ── PRESETS ──────────────────────────────────────────────────────────────────

class TestPresets:
    def test_all_presets_have_description(self):
        for name, preset in PRESETS.items():
            assert "description" in preset, f"Preset '{name}' missing description"
            assert "commands" in preset, f"Preset '{name}' missing commands"
            assert "gui" in preset, f"Preset '{name}' missing gui flag"

    def test_preset_names(self):
        expected = {"cinematic_dark", "cinematic_wide", "educational", "observation", "screenshot", "default"}
        assert set(PRESETS.keys()) == expected

    def test_cinematic_dark_hides_gui(self):
        assert PRESETS["cinematic_dark"]["gui"] is False

    def test_educational_shows_overlays(self):
        cmds = PRESETS["educational"]["commands"]
        assert "Show Labels" in cmds
        assert "Show Orbits" in cmds
        assert "Show Constellations" in cmds

    def test_default_restores_gui(self):
        assert PRESETS["default"]["gui"] is True


# ── _extract_object_info_from_log ────────────────────────────────────────────

class TestExtractObjectInfo:
    def test_extracts_selected_info(self):
        entries = [
            {"message": "Selected object: Earth"},
            {"message": "Distance to Earth: 12756 km"},
            {"message": "Some unrelated log"},
        ]
        info = _extract_object_info_from_log(entries, "Earth")
        assert "last_selected" in info
        assert "distance_info" in info

    def test_no_match(self):
        entries = [{"message": "Nothing here"}]
        info = _extract_object_info_from_log(entries, "Mars")
        assert info == {}

    def test_case_insensitive(self):
        entries = [{"message": "SELECTED earth object"}]
        info = _extract_object_info_from_log(entries, "Earth")
        assert "last_selected" in info


# ── 장면 관리 (save/load/list) — 파일시스템 테스트 ───────────────────────────

class TestSceneFiles:
    def test_scene_json_roundtrip(self, tmp_path):
        """JSON 저장/로드 라운드트립"""
        scene_data = {
            "name": "test_scene",
            "description": "Test",
            "created_at": "2024-01-01 00:00:00",
            "selected_object": "Mars",
            "camera": {"fov": 45},
        }
        scene_file = tmp_path / "test_scene.json"
        scene_file.write_text(json.dumps(scene_data, ensure_ascii=False, indent=2), encoding="utf-8")

        loaded = json.loads(scene_file.read_text(encoding="utf-8"))
        assert loaded["name"] == "test_scene"
        assert loaded["selected_object"] == "Mars"

    def test_list_scenes_empty(self, tmp_path):
        """비어있는 디렉토리"""
        scenes = list(tmp_path.glob("*.json"))
        assert len(scenes) == 0

    def test_list_scenes_with_files(self, tmp_path):
        """여러 장면 파일"""
        for name in ["scene1", "scene2", "scene3"]:
            (tmp_path / f"{name}.json").write_text(
                json.dumps({"name": name}), encoding="utf-8",
            )
        scenes = list(tmp_path.glob("*.json"))
        assert len(scenes) == 3
