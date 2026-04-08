"""
.se / .sc 파일 생성 수동 테스트 스크립트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import tempfile
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge
from spaceengine_mcp.bridges.catalog_bridge import CatalogBridge, CelestialObject

# 임시 디렉토리를 SE 설치 경로로 사용
tmp = Path(tempfile.mkdtemp())
config = SpaceEngineConfig(install_path=tmp)
templates_dir = str(Path(__file__).parent / "templates")
bridge = ScriptBridge(config, templates_dir=templates_dir)
cat_bridge = CatalogBridge(config)

# ── 1) 내비게이션 스크립트 ──────────────────────────────────────────────────
cmds = bridge.build_navigation_commands("Mars", mode="goto", distance_rad=3.0, transition_time=5.0)
path1 = bridge.generate_script(cmds, filename="test_navigate.se")
print("=== 1) navigate_to Mars ===")
print(path1.read_text(encoding="utf-8"))
print()

# ── 2) 시간 설정 스크립트 ──────────────────────────────────────────────────
cmds2 = bridge.build_time_commands(date_iso="2024-04-08T18:00:00", rate=1000)
path2 = bridge.generate_script(cmds2, filename="test_time.se")
print("=== 2) set_time ===")
print(path2.read_text(encoding="utf-8"))
print()

# ── 3) 오버레이 토글 ──────────────────────────────────────────────────────
cmds3 = (
    bridge.build_overlay_commands("Orbits", True)
    + bridge.build_overlay_commands("Labels", False)
    + bridge.build_overlay_commands("Constellations", True)
)
path3 = bridge.generate_script(cmds3, filename="test_overlay.se")
print("=== 3) toggle_overlay ===")
print(path3.read_text(encoding="utf-8"))
print()

# ── 4) Jinja2 투어 템플릿 ─────────────────────────────────────────────────
stops = [
    {"target": "Sol",     "wait_seconds": 5,  "distance_rad": 20.0, "message": "우리의 태양입니다!"},
    {"target": "Mercury", "wait_seconds": 10, "distance_rad": 5.0,  "message": "가장 가까운 행성 수성"},
    {"target": "Venus",   "wait_seconds": 10, "distance_rad": 5.0,  "message": "뜨거운 금성"},
    {"target": "Earth",   "wait_seconds": 10, "distance_rad": 5.0,  "message": "우리의 고향 지구"},
    {"target": "Mars",    "wait_seconds": 10, "distance_rad": 5.0,  "message": "붉은 행성 화성"},
]
ctx = {"title": "초등학생 태양계 투어", "stops": stops, "loop": False, "transition_time": 5.0}
path4 = bridge.generate_from_template("tour.se.j2", ctx)
print("=== 4) 교육 투어 스크립트 (tour.se.j2) ===")
print(path4.read_text(encoding="utf-8"))
print()

# ── 5) 커스텀 항성계 .sc 카탈로그 ────────────────────────────────────────
star = CelestialObject(
    obj_type="Star",
    name="MCP_TestSol",
    properties={
        "Class": '"G2 V"',
        "Mass": "1.0",
        "Radius": "1.0",
        "Temperature": "5778",
        "Luminosity": "1.0",
    },
)
planet_b = CelestialObject(
    obj_type="Planet",
    name="MCP_TestSol b",
    parent_body="MCP_TestSol",
    properties={
        "Class": '"Terra"',
        "Mass": "0.9",
        "Radius": "6200",
        "Orbit": {"SemiMajorAxis": "0.95", "Period": "0.92", "Eccentricity": "0.02", "Inclination": "1.0"},
    },
)
planet_c = CelestialObject(
    obj_type="Planet",
    name="MCP_TestSol c",
    parent_body="MCP_TestSol",
    properties={
        "Class": '"Terra"',
        "Mass": "1.2",
        "Radius": "6800",
        "Orbit": {"SemiMajorAxis": "1.4", "Period": "1.65", "Eccentricity": "0.05", "Inclination": "2.3"},
    },
)
star_path = cat_bridge.write_star_catalog([star], catalog_name="TestSystem")
planet_path = cat_bridge.write_planet_catalog([planet_b, planet_c], catalog_name="TestSystem")

print("=== 5) 항성 카탈로그 (.sc) ===")
print(star_path.read_text(encoding="utf-8"))
print()
print("=== 6) 행성 카탈로그 (.sc) ===")
print(planet_path.read_text(encoding="utf-8"))
print()

print(f"생성된 .se 파일 위치: {config.scripts_dir}")
print(f"생성된 항성 카탈로그: {star_path}")
print(f"생성된 행성 카탈로그: {planet_path}")
