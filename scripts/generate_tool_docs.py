"""59개 MCP Tool의 레퍼런스 문서를 자동 생성"""
import sys
sys.path.insert(0, "src")

from spaceengine_mcp.server import mcp

output_lines = [
    "# Tool Reference",
    "",
    f"Total: **{len(mcp._tool_manager._tools)}** tools",
    "",
]

# Phase별 그룹핑
phase_map = {
    "Phase 1 — Navigation": ["navigate_to", "run_script", "search_catalog"],
    "Phase 2 — Creation": ["create_star", "create_planet", "create_tour", "set_time", "toggle_overlay", "list_addons", "delete_addon"],
    "Phase 3 — Camera": ["control_camera", "take_screenshot", "show_message", "hide_message", "toggle_gui", "follow_object", "read_log"],
    "Phase 4 — Advanced": ["play_sound", "stop_sound", "save_state", "restore_state", "create_flyby", "create_comparison", "set_rendering", "wait_and_execute"],
    "Phase 5 — Console": ["set_variable", "interpolate_variable", "create_spline_path", "manage_waypoints", "camera_flight", "set_speed", "fade_effect", "manage_dialogs", "advanced_message"],
    "Phase 6 — Catalog": ["create_moon", "create_barycenter", "create_ring_system", "edit_atmosphere", "edit_surface", "create_nebula", "create_galaxy", "search_catalog_v2"],
    "Phase 7 — Keyboard": ["record_video", "search_object", "hi_res_screenshot", "switch_mode", "keyboard_shortcut"],
    "Phase 8 — Filesystem": ["edit_config", "manage_addons", "create_spacecraft", "export_object_data"],
    "Phase 9 — Intelligence": ["read_se_state", "verify_command", "screen_capture_ocr", "smart_navigation"],
    "Phase 10 — Flight": ["pilot_spacecraft", "autopilot_control", "docking_assist", "flight_hud_read"],
}

tools = mcp._tool_manager._tools

for phase_name, tool_names in phase_map.items():
    output_lines.append(f"## {phase_name}")
    output_lines.append("")
    for name in tool_names:
        tool = tools.get(name)
        if tool:
            desc = (tool.description or "").split("\n")[0].strip()
            output_lines.append(f"### `{name}`")
            output_lines.append(f"{desc}")
            output_lines.append("")

# 분류되지 않은 도구
classified = set()
for names in phase_map.values():
    classified.update(names)
unclassified = set(tools.keys()) - classified
if unclassified:
    output_lines.append("## Other")
    output_lines.append("")
    for name in sorted(unclassified):
        tool = tools[name]
        desc = (tool.description or "").split("\n")[0].strip()
        output_lines.append(f"### `{name}`")
        output_lines.append(f"{desc}")
        output_lines.append("")

# 파일 출력
docs_dir = "docs_site"
with open(f"{docs_dir}/tools.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"Generated docs_site/tools.md with {len(tools)} tools")
