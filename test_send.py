"""단일 명령 전달 스크립트 — 인수로 테스트 선택"""
import sys
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
EXE = str(SE_PATH / "system" / "SpaceEngine.exe")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir=str(Path(__file__).parent / "templates"))

# python test_send.py <테스트명>
# 예: python test_send.py mars
key = sys.argv[1] if len(sys.argv) > 1 else "mars"

cases = {
    "mars":    bridge.build_navigation_commands("Mars",    "goto", 3.0),
    "sol":     bridge.build_navigation_commands("Sol",     "goto", 50.0),
    "jupiter": bridge.build_navigation_commands("Jupiter", "goto", 5.0),
    "saturn":  bridge.build_navigation_commands("Saturn",  "goto", 8.0),
    "earth":   bridge.build_navigation_commands("Earth",   "goto", 5.0),
    "orbits_on":  bridge.build_overlay_commands("Orbits", True),
    "orbits_off": bridge.build_overlay_commands("Orbits", False),
    "labels_on":  bridge.build_overlay_commands("Labels", True),
    "labels_off": bridge.build_overlay_commands("Labels", False),
    "time_fast": bridge.build_time_commands(rate=10000),
    "time_stop": bridge.build_time_commands(rate=0),
    "time_real": bridge.build_time_commands(rate=1),
    # Phase 3 — 카메라/스크린샷/메시지/UI
    "zoom_in":     bridge.build_camera_commands(dist_rad=2.0, time=3.0),
    "zoom_out":    bridge.build_camera_commands(dist_rad=20.0, time=3.0),
    "fov_wide":    bridge.build_camera_commands(fov=90.0),
    "fov_narrow":  bridge.build_camera_commands(fov=10.0),
    "screenshot":  bridge.build_screenshot_command(),
    "msg_hello":   bridge.build_message_commands("Hello SpaceEngine!", duration=5.0),
    "msg_hide":    bridge.build_message_commands("", show=False),
    "gui_hide":    bridge.build_gui_commands(False),
    "gui_show":    bridge.build_gui_commands(True),
    "follow_mars": bridge.build_follow_commands("Mars", mode="follow"),
    "track_mars":  bridge.build_follow_commands("Mars", mode="track"),
    "unfollow":    bridge.build_follow_commands("", mode="unfollow"),
    # Phase 4 — 상태 저장/복원, 렌더링
    "save":    ["SaveVars"],
    "restore": ["RestoreVars"],
    "atmo_off":  ["Hide Atmosphere"],
    "atmo_on":   ["Show Atmosphere"],
    "cloud_off": ["Hide Clouds"],
    "cloud_on":  ["Show Clouds"],
    # Phase 5 — 변수, 비행, 페이드, 속도
    "set_var":      bridge.build_variable_commands("StarBrightness", "set", "2.0"),
    "reset_var":    bridge.build_variable_commands("StarBrightness", "reset"),
    "interp":       bridge.build_interpolate_commands("StarBrightness", 0.5, 3.0, "linear"),
    "fly_forward":  bridge.build_flight_commands("fly", 0, 0, 1),
    "stop_fly":     bridge.build_flight_commands("stop_fly"),
    "speed_km":     bridge.build_speed_commands(1000, "km"),
    "fade_out":     bridge.build_fade_commands("fade_out", 2.0),
    "fade_in":      bridge.build_fade_commands("fade_in", 1.0),
    "dialog_info":  bridge.build_dialog_commands("ObjectInfo", "show"),
    "dialog_hide":  bridge.build_dialog_commands(action="hide_all"),
    "adv_msg":      bridge.build_advanced_message_commands("Hello [b]SE[/b]!", False, 5.0),
    "waypoint":     bridge.build_waypoint_commands("TestWP", "create"),
    "wp_goto":      bridge.build_waypoint_commands("TestWP", "goto"),
    "wp_clear":     bridge.build_waypoint_commands(mode="clear_all"),
}

if key == "tour":
    stops = [
        {"target": "Sol",     "wait_seconds": 8, "distance_rad": 20.0, "message": "우리의 태양입니다!"},
        {"target": "Mercury", "wait_seconds": 8, "distance_rad": 5.0,  "message": "수성 - 태양에 가장 가까운 행성"},
        {"target": "Venus",   "wait_seconds": 8, "distance_rad": 5.0,  "message": "금성 - 뜨거운 행성"},
        {"target": "Earth",   "wait_seconds": 8, "distance_rad": 5.0,  "message": "지구 - 우리의 고향"},
        {"target": "Mars",    "wait_seconds": 8, "distance_rad": 5.0,  "message": "화성 - 붉은 행성"},
        {"target": "Jupiter", "wait_seconds": 8, "distance_rad": 5.0,  "message": "목성 - 태양계 최대 행성"},
        {"target": "Saturn",  "wait_seconds": 8, "distance_rad": 8.0,  "message": "토성 - 아름다운 고리"},
    ]
    ctx = {"title": "태양계투어", "stops": stops, "loop": False, "transition_time": 4.0}
    path = bridge.generate_from_template("tour.se.j2", ctx)
elif key in cases:
    path = bridge.generate_script(cases[key], filename=f"mcp_{key}.se")
else:
    print(f"알 수 없는 테스트: {key}")
    print("사용 가능:", list(cases.keys()) + ["tour"])
    sys.exit(1)

content = path.read_text(encoding="utf-8")
print(f"전달: {path.name}")
print(content)

lines = content.splitlines()
result = send_commands_via_console(lines)
print(f"결과: {result}")
