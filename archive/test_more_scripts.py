"""추가 .se 스크립트 생성 및 실행 테스트"""
import sys, io, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
EXE = str(SE_PATH / "system" / "SpaceEngine.exe")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir="templates")


def send(name: str, cmds: list[str]) -> Path:
    path = bridge.generate_script(cmds, filename=f"mcp_{name}.se")
    subprocess.Popen([EXE, str(path)])
    print(f"[전달됨] {name}.se")
    for c in cmds:
        print(f"  {c}")
    print()
    return path


menu = {
    "1": ("화성 이동",    lambda: bridge.build_navigation_commands("Mars",    "goto", 3.0)),
    "2": ("태양 이동",    lambda: bridge.build_navigation_commands("Sol",     "goto", 50.0)),
    "3": ("목성 이동",    lambda: bridge.build_navigation_commands("Jupiter", "goto", 5.0)),
    "4": ("토성 이동",    lambda: bridge.build_navigation_commands("Saturn",  "goto", 5.0)),
    "5": ("지구 이동",    lambda: bridge.build_navigation_commands("Earth",   "goto", 5.0)),
    "6": ("궤도선 켜기",  lambda: bridge.build_overlay_commands("Orbits", True)),
    "7": ("궤도선 끄기",  lambda: bridge.build_overlay_commands("Orbits", False)),
    "8": ("시간 x1000",   lambda: bridge.build_time_commands(rate=1000)),
    "9": ("시간 일시정지",lambda: bridge.build_time_commands(rate=0)),
    "r": ("실시간 복귀",  lambda: bridge.build_time_commands(rate=1)),
    "t": ("투어 시작",    None),
}

print("=== SpaceEngine MCP 스크립트 테스트 ===")
print("(SpaceEngine이 완전히 로드된 후 번호를 입력하세요)\n")
for k, (desc, _) in menu.items():
    print(f"  {k}) {desc}")
print()

while True:
    key = input("번호 입력 (q=종료): ").strip().lower()
    if key == "q":
        break
    if key not in menu:
        print("없는 번호입니다.")
        continue

    desc, fn = menu[key]

    if key == "t":
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
        subprocess.Popen([EXE, str(path)])
        print(f"[전달됨] 태양계 투어 -> {path.name}\n")
    else:
        send(key + "_" + desc.replace(" ", "_"), fn())
