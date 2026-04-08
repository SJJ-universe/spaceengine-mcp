"""
SpaceEngine MCP 전체 기능 디버그 테스트
- 콘솔 스크린샷 캡처로 SE 내부 에러 확인
- se.log 파싱으로 로그 레벨 디버깅
- 각 테스트 케이스별 before/after 스크린샷

실행: python test_full_debug.py [그룹명]
  그룹: all, nav, camera, time, overlay, message, gui, follow, render, state, fade, var, flight, tour
"""
import ctypes
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import ImageGrab
import win32gui

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console, find_se_window
from spaceengine_mcp.bridges.log_bridge import (
    parse_log_tail, get_log_errors, get_log_stats, get_selected_object, get_camera_info,
)

# ── 설정 ───────────────────────────────────────────────────────────────────
SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
LOG_PATH = SE_PATH / "system" / "se.log"
CAPTURE_DIR = Path(__file__).parent / "test_captures" / datetime.now().strftime("%Y%m%d_%H%M%S")

config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir=str(Path(__file__).parent / "templates"))

# ── 유틸리티 ───────────────────────────────────────────────────────────────

def ensure_dir():
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)


def capture_screenshot(name: str) -> str | None:
    """SE 창 영역 스크린샷 캡처"""
    hwnd = find_se_window()
    if not hwnd:
        print("    ⚠ SE 창 없음 — 스크린샷 건너뜀")
        return None
    try:
        rect = win32gui.GetWindowRect(hwnd)
        img = ImageGrab.grab(bbox=rect)
        path = CAPTURE_DIR / f"{name}.png"
        img.save(str(path))
        return str(path)
    except Exception as e:
        print(f"    ⚠ 스크린샷 실패: {e}")
        return None


def capture_console(name: str) -> str | None:
    """SE 콘솔을 열어 스크린샷 캡쳐 후 닫기"""
    hwnd = find_se_window()
    if not hwnd:
        return None
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        # 콘솔 열기 (틸드)
        ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
        time.sleep(1.0)
        # 캡처
        rect = win32gui.GetWindowRect(hwnd)
        img = ImageGrab.grab(bbox=rect)
        path = CAPTURE_DIR / f"console_{name}.png"
        img.save(str(path))
        # 콘솔 닫기
        ctypes.windll.user32.keybd_event(0xC0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0xC0, 0, 2, 0)
        time.sleep(0.5)
        return str(path)
    except Exception as e:
        print(f"    ⚠ 콘솔 캡처 실패: {e}")
        return None


def get_log_snapshot() -> dict:
    """현재 로그 상태 스냅샷"""
    if not LOG_PATH.exists():
        return {"errors": [], "stats": {}, "selected": None, "camera": None}
    return {
        "errors": get_log_errors(LOG_PATH, max_results=5),
        "stats": get_log_stats(LOG_PATH),
        "selected": get_selected_object(LOG_PATH),
        "camera": get_camera_info(LOG_PATH),
    }


# SE 자체의 무해한 경고 — false positive 필터
_BENIGN_LOG_PATTERNS = [
    "Translation not found",
    "MT WARNING",
    "Shader compile",
    "texture not found",
]


def check_new_errors(before_stats: dict, after_stats: dict) -> list:
    """테스트 전후 새 에러 발생 여부 (SE 자체 경고 제외)"""
    before_err = before_stats.get("stats", {}).get("errors", 0)
    before_warn = before_stats.get("stats", {}).get("warnings", 0)
    after_err = after_stats.get("stats", {}).get("errors", 0)
    after_warn = after_stats.get("stats", {}).get("warnings", 0)

    total_before = before_err + before_warn
    total_after = after_err + after_warn

    if total_after > total_before:
        raw_errors = get_log_errors(LOG_PATH, max_results=total_after - total_before)
        # SE 자체 무해한 경고 필터링
        return [
            e for e in raw_errors
            if not any(pat.lower() in e.get("message", "").lower() for pat in _BENIGN_LOG_PATTERNS)
        ]
    return []


# ── 테스트 케이스 정의 ─────────────────────────────────────────────────────

def define_tests():
    return {
        "nav": [
            ("nav_earth", bridge.build_navigation_commands("Earth", "goto", 5.0), 7,
             "Earth로 이동"),
            ("nav_mars", bridge.build_navigation_commands("Mars", "goto", 5.0), 7,
             "Mars로 이동"),
            ("nav_saturn", bridge.build_navigation_commands("Saturn", "goto", 8.0), 10,
             "Saturn으로 이동"),
            ("nav_jupiter", bridge.build_navigation_commands("Jupiter", "goto", 5.0), 7,
             "Jupiter로 이동"),
        ],
        "camera": [
            ("cam_zoom_in", bridge.build_camera_commands(dist_rad=2.0, time=3.0), 5,
             "줌인 (DistRad 2.0)"),
            ("cam_zoom_out", bridge.build_camera_commands(dist_rad=10.0, time=3.0), 5,
             "줌아웃 (DistRad 10.0)"),
            ("cam_fov_wide", bridge.build_camera_commands(fov=90.0), 3,
             "광각 FOV 90"),
            ("cam_fov_narrow", bridge.build_camera_commands(fov=30.0), 3,
             "협각 FOV 30"),
            ("cam_fov_default", bridge.build_camera_commands(fov=45.0), 2,
             "기본 FOV 45 복원"),
        ],
        "time": [
            ("time_fast", bridge.build_time_commands(rate=10000), 3,
             "시간 가속 10000x"),
            ("time_stop", bridge.build_time_commands(rate=0), 2,
             "시간 정지 (StopTime)"),
            ("time_real", bridge.build_time_commands(rate=1), 2,
             "실시간 복원"),
        ],
        "overlay": [
            ("orbits_on", bridge.build_overlay_commands("Orbits", True), 2,
             "궤도선 표시"),
            ("labels_on", bridge.build_overlay_commands("Labels", True), 2,
             "레이블 표시"),
            ("constellations_on", bridge.build_overlay_commands("Constellations", True), 2,
             "별자리 표시"),
            ("constellations_off", bridge.build_overlay_commands("Constellations", False), 2,
             "별자리 숨기기"),
            ("labels_off", bridge.build_overlay_commands("Labels", False), 2,
             "레이블 숨기기"),
            ("orbits_off", bridge.build_overlay_commands("Orbits", False), 2,
             "궤도선 숨기기"),
        ],
        "message": [
            ("msg_show", bridge.build_message_commands("MCP 디버그 테스트 중!", duration=5.0), 6,
             "화면 메시지 표시"),
            ("msg_hide", bridge.build_message_commands("", show=False), 2,
             "메시지 숨기기"),
        ],
        "gui": [
            ("gui_hide", bridge.build_gui_commands(False), 3,
             "GUI 숨기기 (Set ShowGUI false)"),
            ("gui_show", bridge.build_gui_commands(True), 3,
             "GUI 복원 (Set ShowGUI true)"),
        ],
        "follow": [
            ("follow_earth", bridge.build_follow_commands("Earth", mode="follow"), 4,
             "Earth Follow 모드"),
            ("track_earth", bridge.build_follow_commands("Earth", mode="track"), 4,
             "Earth Track 모드"),
            ("unfollow", bridge.build_follow_commands("", mode="unfollow"), 2,
             "추적 해제 (Free)"),
        ],
        "render": [
            ("atmo_off", bridge.build_overlay_commands("Atmosphere", False), 3,
             "대기 숨기기"),
            ("atmo_on", bridge.build_overlay_commands("Atmosphere", True), 3,
             "대기 복원"),
            ("cloud_off", bridge.build_overlay_commands("Clouds", False), 3,
             "구름 숨기기"),
            ("cloud_on", bridge.build_overlay_commands("Clouds", True), 3,
             "구름 복원"),
        ],
        "state": [
            ("save_vars", ["SaveVars"], 2,
             "변수 상태 저장"),
            ("change_after_save", bridge.build_navigation_commands("Mars", "goto", 5.0), 7,
             "Mars로 이동 (저장 후 변경)"),
            ("restore_vars", ["RestoreVars"], 5,
             "변수 상태 복원"),
        ],
        "fade": [
            ("fade_out", bridge.build_fade_commands("fade_out", 2.0), 4,
             "화면 페이드 아웃"),
            ("fade_in", bridge.build_fade_commands("fade_in", 1.5), 3,
             "화면 페이드 인"),
        ],
        "var": [
            ("var_set", bridge.build_variable_commands("StarBrightness", "set", "2.0"), 3,
             "StarBrightness = 2.0"),
            ("var_interpolate", bridge.build_interpolate_commands("StarBrightness", 0.5, 3.0, "linear"), 5,
             "StarBrightness 보간 → 0.5"),
            ("var_reset", bridge.build_variable_commands("StarBrightness", "reset"), 2,
             "StarBrightness 리셋"),
        ],
        "flight": [
            ("fly_forward", bridge.build_flight_commands("fly", 0, 0, 1), 3,
             "전방 비행"),
            ("stop_fly", bridge.build_flight_commands("stop_fly"), 2,
             "비행 정지"),
        ],
    }


# ── 메인 테스트 러너 ───────────────────────────────────────────────────────

def run_test_group(group_name: str, tests: list, results: list):
    """테스트 그룹 실행 — 각 케이스별 before/after 캡처 + 로그 디버그"""
    print(f"\n{'─'*60}")
    print(f"  그룹: {group_name.upper()}")
    print(f"{'─'*60}")

    for i, (name, cmds, wait, desc) in enumerate(tests, 1):
        print(f"\n  [{i}/{len(tests)}] {name} — {desc}")
        print(f"    명령어: {cmds}")

        # Before: 로그 스냅샷 + 게임 화면 캡처
        log_before = get_log_snapshot()
        capture_screenshot(f"{group_name}_{name}_before")

        # 명령 실행
        t0 = time.time()
        script_path = bridge.generate_script(cmds, filename=f"dbg_{name}.se")
        lines = script_path.read_text(encoding="utf-8").splitlines()
        result = send_commands_via_console(lines)
        elapsed = time.time() - t0

        status = result.get("status", "unknown")
        executed = result.get("executed", [])
        count = result.get("count", 0)

        # 대기
        if wait > 0:
            time.sleep(wait)

        # After: 로그 스냅샷 + 게임 화면 캡처
        log_after = get_log_snapshot()
        capture_screenshot(f"{group_name}_{name}_after")

        # 새 에러 체크
        new_errors = check_new_errors(log_before, log_after)

        # 현재 SE 상태
        selected = log_after.get("selected")
        camera = log_after.get("camera")

        # 결과 판정
        ok = status == "ok" and len(new_errors) == 0
        symbol = "✅" if ok else "❌" if status != "ok" else "⚠️"

        print(f"    {symbol} status={status}, 실행={count}개, 시간={elapsed:.1f}s")
        if executed:
            print(f"    ✓ 실행됨: {executed}")
        if selected:
            print(f"    📍 선택된 천체: {selected}")
        if camera:
            print(f"    📷 카메라: {camera}")
        if new_errors:
            print(f"    🔴 새 에러 {len(new_errors)}개:")
            for err in new_errors:
                print(f"       {err}")

        results.append({
            "group": group_name,
            "name": name,
            "desc": desc,
            "ok": ok,
            "status": status,
            "executed": executed,
            "count": count,
            "elapsed": elapsed,
            "new_errors": len(new_errors),
            "selected": selected,
            "camera": camera,
        })


def run_tour_test(results: list):
    """투어 테스트 (별도 — 스크립트 파일 실행)"""
    print(f"\n{'─'*60}")
    print(f"  그룹: TOUR")
    print(f"{'─'*60}")

    stops = [
        {"target": "Sol",     "wait_seconds": 6, "distance_rad": 20.0, "message": "태양!"},
        {"target": "Earth",   "wait_seconds": 6, "distance_rad": 5.0,  "message": "지구!"},
        {"target": "Mars",    "wait_seconds": 6, "distance_rad": 5.0,  "message": "화성!"},
        {"target": "Jupiter", "wait_seconds": 6, "distance_rad": 5.0,  "message": "목성!"},
        {"target": "Saturn",  "wait_seconds": 6, "distance_rad": 8.0,  "message": "토성!"},
    ]
    ctx = {"title": "디버그투어", "stops": stops, "loop": False, "transition_time": 3.0}

    log_before = get_log_snapshot()
    capture_screenshot("tour_before")

    try:
        path = bridge.generate_from_template("tour.se.j2", ctx)
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        print(f"  투어 스크립트: {path.name} ({len(lines)} 줄)")

        t0 = time.time()
        result = send_commands_via_console(lines)
        elapsed = time.time() - t0

        # 투어는 총 대기시간 계산
        total_wait = sum(s["wait_seconds"] for s in stops) + len(stops) * 3.0
        print(f"  ⏳ 투어 완료 대기 {total_wait:.0f}초...")
        time.sleep(total_wait)

        capture_screenshot("tour_after")
        log_after = get_log_snapshot()
        new_errors = check_new_errors(log_before, log_after)

        status = result.get("status", "unknown")
        ok = status == "ok" and len(new_errors) == 0
        symbol = "✅" if ok else "❌"
        print(f"  {symbol} 투어 완료 — status={status}, 에러={len(new_errors)}")

        results.append({
            "group": "tour", "name": "solar_system_tour", "desc": "태양계 투어",
            "ok": ok, "status": status, "executed": result.get("executed", []),
            "count": result.get("count", 0), "elapsed": elapsed + total_wait,
            "new_errors": len(new_errors), "selected": log_after.get("selected"),
            "camera": log_after.get("camera"),
        })
    except Exception as e:
        print(f"  ❌ 투어 실행 실패: {e}")
        results.append({
            "group": "tour", "name": "solar_system_tour", "desc": "태양계 투어",
            "ok": False, "status": "error", "executed": [],
            "count": 0, "elapsed": 0, "new_errors": 1,
            "selected": None, "camera": None,
        })


def print_summary(results: list):
    """테스트 결과 요약 출력"""
    print(f"\n{'='*60}")
    print("  테스트 결과 요약")
    print(f"{'='*60}")

    groups = {}
    for r in results:
        g = r["group"]
        if g not in groups:
            groups[g] = []
        groups[g].append(r)

    total_pass = 0
    total_fail = 0
    for g, items in groups.items():
        passed = sum(1 for r in items if r["ok"])
        failed = len(items) - passed
        total_pass += passed
        total_fail += failed
        print(f"\n  [{g.upper()}] {passed}/{len(items)}")
        for r in items:
            symbol = "✅" if r["ok"] else "❌"
            extra = ""
            if r["new_errors"] > 0:
                extra = f" (에러 {r['new_errors']}개)"
            print(f"    {symbol} {r['name']:25s} {r['desc']}{extra}")

    total = total_pass + total_fail
    print(f"\n{'─'*60}")
    print(f"  합계: {total_pass}/{total} 성공, {total_fail} 실패")
    print(f"  스크린샷: {CAPTURE_DIR}")
    print(f"{'='*60}\n")

    return total_fail == 0


def save_results(results: list):
    """결과를 JSON으로 저장"""
    path = CAPTURE_DIR / "results.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  결과 JSON: {path}")


def capture_final_console():
    """테스트 종료 후 최종 콘솔 상태 캡처"""
    print("\n  📸 최종 콘솔 상태 캡처...")
    capture_console("final")
    print(f"  → {CAPTURE_DIR / 'console_final.png'}")


# ── 엔트리포인트 ───────────────────────────────────────────────────────────

def main():
    group_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    all_tests = define_tests()

    # SE 실행 확인
    hwnd = find_se_window()
    if not hwnd:
        print("❌ SpaceEngine이 실행되고 있지 않습니다!")
        print("   SE를 먼저 실행한 후 다시 시도하세요.")
        sys.exit(1)

    ensure_dir()
    print(f"\n{'='*60}")
    print(f"  SpaceEngine MCP 전체 디버그 테스트")
    print(f"  시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  캡처 폴더: {CAPTURE_DIR}")
    print(f"  테스트 그룹: {group_arg}")
    print(f"{'='*60}")

    # 초기 상태 캡처
    print("\n  📸 초기 상태 캡처...")
    capture_screenshot("00_initial")
    log_initial = get_log_snapshot()
    print(f"  로그 통계: {log_initial.get('stats', {})}")
    print(f"  선택된 천체: {log_initial.get('selected', 'N/A')}")

    results = []

    if group_arg == "all":
        # 전체 순서대로 실행
        order = ["nav", "camera", "time", "overlay", "message",
                 "gui", "follow", "render", "state", "fade", "var", "flight"]
        for g in order:
            if g in all_tests:
                run_test_group(g, all_tests[g], results)

        # 최종 콘솔 스크린샷
        capture_final_console()

        # 투어 테스트 (선택)
        print("\n  투어 테스트도 실행합니까? (약 45초 소요)")
        print("  (3초 내 Ctrl+C로 건너뛰기...)")
        try:
            time.sleep(3)
            run_tour_test(results)
        except KeyboardInterrupt:
            print("  → 투어 건너뜀")

    elif group_arg == "tour":
        run_tour_test(results)
    elif group_arg in all_tests:
        run_test_group(group_arg, all_tests[group_arg], results)
        capture_final_console()
    else:
        print(f"  알 수 없는 그룹: {group_arg}")
        print(f"  사용 가능: {', '.join(list(all_tests.keys()) + ['all', 'tour'])}")
        sys.exit(1)

    # 결과 출력 및 저장
    save_results(results)
    success = print_summary(results)

    if not success:
        print("  💡 실패한 테스트의 스크린샷/로그를 확인하세요:")
        for r in results:
            if not r["ok"]:
                grp = r["group"]
                nm = r["name"]
                print(f"     - {nm}: {CAPTURE_DIR / f'{grp}_{nm}_after.png'}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
