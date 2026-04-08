"""Dry-run: comprehensive 테스트 명령어 validation 확인"""
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge, validate_commands

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir=str(Path("templates")))

test_groups = [
    ("nav_earth", bridge.build_navigation_commands("Earth", "goto", 5.0)),
    ("orbits_on", bridge.build_overlay_commands("Orbits", True)),
    ("zoom_in", bridge.build_camera_commands(dist_rad=2.0, time=3.0)),
    ("fov_wide", bridge.build_camera_commands(fov=90.0)),
    ("time_fast", bridge.build_time_commands(rate=100000)),
    ("time_stop", bridge.build_time_commands(rate=0)),
    ("time_real", bridge.build_time_commands(rate=1)),
    ("msg_hello", bridge.build_message_commands("MCP test", duration=5.0)),
    ("gui_hide", bridge.build_gui_commands(False)),
    ("gui_show", bridge.build_gui_commands(True)),
    ("follow", bridge.build_follow_commands("Earth", mode="follow")),
    ("unfollow", bridge.build_follow_commands("", mode="unfollow")),
    ("atmo_off", bridge.build_overlay_commands("Atmosphere", False)),
    ("atmo_on", bridge.build_overlay_commands("Atmosphere", True)),
    ("screenshot", bridge.build_screenshot_command()),
    ("msg_hide", bridge.build_message_commands("", show=False)),
]

print("=== 명령어 생성 + Validation ===")
all_ok = True
for name, cmds in test_groups:
    blocked = validate_commands(cmds)
    if blocked:
        all_ok = False
        print(f"  FAIL {name:15s} -> BLOCKED: {blocked}")
    else:
        print(f"  OK   {name:15s} -> {cmds}")

print(f"\n결과: {'전체 PASS' if all_ok else 'FAIL 있음'}")
