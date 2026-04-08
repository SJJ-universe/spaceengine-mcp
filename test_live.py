"""
실제 SpaceEngine에 .se 스크립트를 전달하는 라이브 테스트.
SE가 실행 중이어야 스크립트가 즉시 적용됩니다.
"""
import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir=str(Path(__file__).parent / "templates"))

print(f"SE 설치 경로: {config.install_path}")
print(f"스크립트 저장 위치: {config.scripts_dir}")
print(f"실행 파일: {config.executable}")
print()

TESTS = {
    "1": ("화성으로 이동", lambda: bridge.build_navigation_commands("Mars", mode="goto", distance_rad=3.0)),
    "2": ("태양으로 이동 (멀리서)", lambda: bridge.build_navigation_commands("Sol", mode="goto", distance_rad=50.0)),
    "3": ("목성으로 이동", lambda: bridge.build_navigation_commands("Jupiter", mode="goto", distance_rad=5.0)),
    "4": ("궤도 표시 켜기", lambda: bridge.build_overlay_commands("Orbits", True)),
    "5": ("궤도 표시 끄기", lambda: bridge.build_overlay_commands("Orbits", False)),
    "6": ("시간 가속 x1000", lambda: bridge.build_time_commands(rate=1000)),
    "7": ("시간 일시정지", lambda: bridge.build_time_commands(rate=0)),
    "8": ("실시간으로 복귀", lambda: bridge.build_time_commands(rate=1)),
    "9": ("초등학생 태양계 투어", None),  # 투어는 별도 처리
}


async def run_test(key: str):
    if key == "9":
        stops = [
            {"target": "Sol",     "wait_seconds": 8,  "distance_rad": 20.0, "message": "우리의 태양입니다!"},
            {"target": "Mercury", "wait_seconds": 8,  "distance_rad": 5.0,  "message": "수성 - 태양에 가장 가까운 행성"},
            {"target": "Venus",   "wait_seconds": 8,  "distance_rad": 5.0,  "message": "금성 - 뜨거운 행성"},
            {"target": "Earth",   "wait_seconds": 8,  "distance_rad": 5.0,  "message": "지구 - 우리의 고향"},
            {"target": "Mars",    "wait_seconds": 8,  "distance_rad": 5.0,  "message": "화성 - 붉은 행성"},
            {"target": "Jupiter", "wait_seconds": 8,  "distance_rad": 5.0,  "message": "목성 - 태양계 최대 행성"},
            {"target": "Saturn",  "wait_seconds": 8,  "distance_rad": 5.0,  "message": "토성 - 아름다운 고리"},
        ]
        ctx = {"title": "태양계 투어", "stops": stops, "loop": False, "transition_time": 4.0}
        script_path = bridge.generate_from_template("tour.se.j2", ctx)
    else:
        name, cmd_fn = TESTS[key]
        cmds = cmd_fn()
        print(f"명령어:")
        for c in cmds:
            print(f"  {c}")
        script_path = bridge.generate_script(cmds)

    print(f"생성된 파일: {script_path}")
    print("SpaceEngine에 전달 중...")
    result = await bridge.execute_script(script_path, timeout=5.0)
    print(f"결과: {result['status']}")
    if "note" in result:
        print(f"  {result['note']}")
    if result["status"] == "error":
        print(f"  오류: {result['message']}")


async def main():
    print("=== SpaceEngine MCP 라이브 테스트 ===")
    print()
    for k, (desc, _) in TESTS.items():
        print(f"  {k}) {desc}")
    print()
    key = input("실행할 테스트 번호 입력 (기본값: 1): ").strip() or "1"

    if key not in TESTS:
        print("잘못된 번호입니다.")
        return

    name = TESTS[key][0]
    print(f"\n[{name}] 실행 중...\n")
    await run_test(key)


asyncio.run(main())
