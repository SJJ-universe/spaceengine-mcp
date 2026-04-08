"""Tool 등록 검증 — 68개 도구가 올바르게 등록되었는지 확인"""
import pytest

from spaceengine_mcp.server import mcp


def test_total_tool_count():
    """전체 Tool 수 검증"""
    tools = mcp._tool_manager._tools
    assert len(tools) >= 68, f"Expected 68+ tools, got {len(tools)}"


def test_all_tools_have_descriptions():
    """모든 Tool에 description이 있어야 함"""
    tools = mcp._tool_manager._tools
    for name, tool in tools.items():
        assert tool.description, f"Tool '{name}' has no description"


def test_core_tools_registered():
    """핵심 Tool들이 등록되어 있는지 확인"""
    tools = mcp._tool_manager._tools
    expected_core = [
        # Phase 1
        "navigate_to", "run_script", "search_catalog",
        # Phase 2
        "create_star", "create_planet", "create_tour", "set_time", "toggle_overlay",
        # Phase 3
        "control_camera", "take_screenshot", "show_message", "follow_object", "read_log",
        # Phase 4
        "play_sound", "save_state", "restore_state", "create_flyby", "set_rendering",
        # Phase 5
        "set_variable", "interpolate_variable", "create_spline_path",
        "camera_flight", "set_speed", "fade_effect",
        # Phase 6
        "create_moon", "create_nebula", "create_galaxy",
        # Phase 7
        "search_object", "switch_mode", "keyboard_shortcut",
        # Phase 8
        "edit_config", "export_object_data",
        # Phase 9
        "read_se_state", "smart_navigation",
        # Phase 10
        "pilot_spacecraft", "autopilot_control",
        # Phase 11
        "cinematic_sequence", "apply_preset", "get_object_info",
        "timelapse_capture", "save_scene", "load_scene", "list_scenes",
    ]
    registered_names = set(tools.keys())
    for name in expected_core:
        assert name in registered_names, f"Core tool '{name}' not registered"


def test_no_duplicate_tool_names():
    """Tool 이름 중복 없음 확인 (FastMCP가 자체 처리하지만 확인)"""
    tools = mcp._tool_manager._tools
    names = list(tools.keys())
    assert len(names) == len(set(names)), "Duplicate tool names detected"


def test_resources_registered():
    """4개 Resource 등록 확인"""
    resources = mcp._resource_manager._resources
    assert len(resources) == 4


def test_prompts_registered():
    """3개 Prompt 등록 확인"""
    prompts = mcp._prompt_manager._prompts
    assert len(prompts) == 3
