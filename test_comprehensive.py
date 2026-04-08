"""전체 기능 종합 테스트 — 모든 test_send.py 케이스를 순차 실행"""
import time
import sys
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir=str(Path(__file__).parent / "templates"))

# ── 테스트 그룹 정의 ──────────────────────────────────────────────────────────
TESTS = [
    # (이름, 명령어 리스트, 대기 시간(초), 설명)
    # --- 1) 네비게이션 ---
    ("nav_earth",   bridge.build_navigation_commands("Earth", "goto", 5.0), 7,
     "Earth로 이동 (카메라 잠금 해제 + Select + Goto)"),

    # --- 2) 오버레이 ---
    ("orbits_on",   bridge.build_overlay_commands("Orbits", True),  2,
     "궤도선 표시"),
    ("labels_on",   bridge.build_overlay_commands("Labels", True),  2,
     "레이블 표시"),

    # --- 3) 카메라 ---
    ("zoom_in",     bridge.build_camera_commands(dist_rad=2.0, time=3.0), 4,
     "카메라 줌인 (DistRad 2.0)"),
    ("fov_wide",    bridge.build_camera_commands(fov=90.0), 2,
     "광각 FOV 90도"),
    ("fov_narrow",  bridge.build_camera_commands(fov=30.0), 2,
     "협각 FOV 30도 (기본 복원)"),
    ("zoom_out",    bridge.build_camera_commands(dist_rad=5.0, time=3.0), 4,
     "카메라 줌아웃 (DistRad 5.0)"),

    # --- 4) 시간 제어 ---
    ("time_fast",   bridge.build_time_commands(rate=100000), 3,
     "시간 가속 (100000배)"),
    ("time_stop",   bridge.build_time_commands(rate=0), 2,
     "시간 정지"),
    ("time_real",   bridge.build_time_commands(rate=1), 2,
     "실시간 복원"),

    # --- 5) 메시지 ---
    ("msg_hello",   bridge.build_message_commands("MCP 종합 테스트 진행 중!", duration=5.0), 2,
     "화면 메시지 표시"),

    # --- 6) GUI 토글 ---
    ("gui_hide",    bridge.build_gui_commands(False), 2,
     "GUI 숨기기"),
    ("gui_show",    bridge.build_gui_commands(True), 2,
     "GUI 복원"),

    # --- 7) 오버레이 끄기 (원상 복구) ---
    ("orbits_off",  bridge.build_overlay_commands("Orbits", False), 1,
     "궤도선 숨기기"),
    ("labels_off",  bridge.build_overlay_commands("Labels", False), 1,
     "레이블 숨기기"),

    # --- 8) Follow/Track ---
    ("follow_earth", bridge.build_follow_commands("Earth", mode="follow"), 3,
     "Earth 추적 (Follow)"),
    ("unfollow",    bridge.build_follow_commands("", mode="unfollow"), 2,
     "추적 해제"),

    # --- 9) 렌더링 토글 ---
    ("atmo_off",    bridge.build_overlay_commands("Atmosphere", False), 2,
     "대기 숨기기"),
    ("atmo_on",     bridge.build_overlay_commands("Atmosphere", True), 2,
     "대기 복원"),
    ("cloud_off",   bridge.build_overlay_commands("Clouds", False), 2,
     "구름 숨기기"),
    ("cloud_on",    bridge.build_overlay_commands("Clouds", True), 2,
     "구름 복원"),

    # --- 10) Screenshot ---
    ("screenshot",  bridge.build_screenshot_command(), 2,
     "SE 스크린샷 캡처"),

    # --- 11) 상태 저장/복원 ---
    ("save_vars",   ["SaveVars"], 1,
     "변수 상태 저장"),
    ("nav_saturn",  bridge.build_navigation_commands("Saturn", "goto", 8.0), 7,
     "Saturn으로 이동 (저장 후 위치 변경)"),
    ("restore_vars", ["RestoreVars"], 4,
     "변수 상태 복원 (Earth로 돌아오는지?)"),

    # --- 12) 두 번째 네비게이션 (Jupiter) ---
    ("nav_jupiter", bridge.build_navigation_commands("Jupiter", "goto", 5.0), 7,
     "Jupiter로 최종 이동"),

    # --- 메시지 끄기 ---
    ("msg_hide",    bridge.build_message_commands("", show=False), 1,
     "메시지 숨기기"),
]


def run_all():
    results = []
    total = len(TESTS)
    print(f"\n{'='*60}")
    print(f"  SpaceEngine MCP 종합 테스트 — {total}개 케이스")
    print(f"{'='*60}\n")

    for i, (name, cmds, wait, desc) in enumerate(TESTS, 1):
        print(f"[{i:2d}/{total}] {name:20s} — {desc}")
        print(f"         명령어: {cmds}")

        script_path = bridge.generate_script(cmds, filename=f"mcp_test_{name}.se")
        lines = script_path.read_text(encoding="utf-8").splitlines()
        result = send_commands_via_console(lines)

        status = result.get("status", "unknown")
        ok = status == "ok"
        results.append((name, ok, desc, result))

        symbol = "✅" if ok else "❌"
        print(f"         {symbol} {status} (count={result.get('count', 0)})")

        if wait > 0:
            print(f"         ⏳ {wait}초 대기...")
            time.sleep(wait)
        print()

    # ── 결과 요약 ──
    print(f"\n{'='*60}")
    print("  테스트 결과 요약")
    print(f"{'='*60}")
    passed = sum(1 for _, ok, _, _ in results if ok)
    failed = sum(1 for _, ok, _, _ in results if not ok)
    for name, ok, desc, _ in results:
        symbol = "✅" if ok else "❌"
        print(f"  {symbol} {name:20s} — {desc}")
    print(f"\n  합계: {passed} 성공 / {failed} 실패 / {total} 전체")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    run_all()
