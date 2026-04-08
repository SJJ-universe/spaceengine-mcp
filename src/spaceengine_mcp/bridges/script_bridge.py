import asyncio
import time
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from spaceengine_mcp.config import SpaceEngineConfig
try:
    from spaceengine_mcp.bridges.console_bridge import send_commands_via_console
except ImportError:
    # Linux/테스트 환경에서는 pywin32 없음 — 스텁 제공
    def send_commands_via_console(commands, close_console=True):
        return {"status": "error", "message": "pywin32 not available (non-Windows)"}

# ── 허용된 SE 콘솔/스크립트 명령어 (화이트리스트) ─────────────────────────────
# 출처: https://spaceengine.org/manual/making-addons/scenario-scripts/
# 2026-04-06 공식 문서 기준으로 검증 완료
ALLOWED_COMMANDS = {
    # ── User Control (카메라 잠금 해제/잠금) ──
    "UserMoveControl",       # "Free" / "Disabled" / "Limited"
    "UserRotationControl",   # "Free" / "Disabled" / "Limited"
    "UserTimeControl",       # "Free" / "Disabled" / "Limited"
    "UserStereobaseControl", # "Free" / "Disabled" / "Limited"

    # ── Navigation & Selection ──
    "Select", "Unselect",
    "Goto",                  # Goto { Time 5 DistRad 3 Lon 0 Lat 0 }
    "Center",                # Center { Time 2 }
    "Horizon",               # Horizon { Time 2 }
    "GotoLocation",          # GotoLocation "LocationCode"
    "GotoURL",               # GotoURL "url"

    # ── Camera Binding Modes ──
    "Follow",                # 카메라가 천체 중심 추적 (회전 무관)
    "SyncRot",               # 표면 동기 회전 (상대 위치 유지)
    "Track",                 # 시선 고정 (자동 회전)
    "Untrack",               # Track 해제
    "Free",                  # 모든 바인딩 해제

    # ── Camera Movement ──
    "FOV",                   # FOV 90 (시야각 도 단위, 독립 명령)
    "MoveMode",              # 이동 모드 설정
    "Speed", "SpeedKm",      # 이동 속도 설정
    "Fly", "StopFly",        # 부드러운 카메라 비행/중지
    "Turn", "StopTurn",      # 카메라 회전/중지
    "Orbit", "StopOrbit",    # 천체 주위 궤도 운동/중지

    # ── Waypoints ──
    "Waypoint",              # Waypoint "Name" { ... }
    "DeleteWaypoint",        # DeleteWaypoint "Name"
    "ClearWaypoints",        # ClearWaypoints
    "GotoWaypoint",          # GotoWaypoint "Name"

    # ── Spline Paths ──
    "SplinePath",            # SplinePath "Name" { knot definitions }
    "PlaySplinePath",        # PlaySplinePath "Name" / PlaySplinePath "Name" { Time 10 }
    "DeleteSplinePath",      # DeleteSplinePath "Name"
    "ClearSplinePaths",      # ClearSplinePaths
    # 주의: StopSplinePath는 공식 문서에서 확인 필요, 일단 보류
    # 주의: RecordSplinePath는 런타임 녹화용, 스크립트에서 직접 사용 비추

    # ── Time Control ──
    "Date",                  # Date "2024.04.08 18:00:00" (SE 형식)
    "Time",                  # Time은 Date의 동의어
    "TimeScale",             # TimeScale 100.0 (양수=배속, 음수=역방향)
    "StopTime",              # 시간 정지 (Pause 대신 사용)
    "StartTime",             # 시간 재개 (RealTime 대신 사용)

    # ── Triggers / Flow Control ──
    "Wait",                  # Wait 3.5 (초 단위 지연)
    "WaitTrigger",           # WaitTrigger "TriggerName"
    "WaitVar",               # WaitVar VariableName Value
    "BeginMultiTrigger", "EndMultiTrigger",  # 복합 트리거 ("OR" / "AND")
    "Break",                 # 루프/스크립트 중단
    "Loop", "EndLoop",       # 무한 루프
    "if", "elif", "else", "endif",  # 조건문
    "CheckVersion",          # CheckVersion 990 (버전 검사)

    # ── Variables ──
    "SaveVars",              # 현재 변수/툴바 상태 저장
    "RestoreVars",           # 저장된 상태 복원 (스크립트 종료 시 자동 호출)
    "Set",                   # Set VarName value (범위 검사 포함)
    "SetU",                  # SetU VarName value (범위 검사 없음)
    "SetForce",              # SetForce VarName value (강제 설정)
    "Reset",                 # Reset VarName (기본값 복원)
    "Interpolate",           # Interpolate Var { To val Time dur Func "type" }

    # ── Rendering / Visibility ──
    "Show",                  # Show Clouds / Show Orbits 등 (파라미터: 복수형 사용)
    "Hide",                  # Hide Atmospheres / Hide Labels 등
    "Toggle",                # Toggle VarName (불리언 변수 토글)
    "ShowObject", "HideObject",  # 특정 오브젝트 표시/숨김
    "FadeOut", "FadeIn",     # 화면 페이드 효과

    # ── Interface / Messages ──
    "Print", "HidePrint",           # 화면 텍스트 표시/숨김 (스크립트 계속 진행)
    "ShowMessage", "HideMessage",   # 메시지 박스 (BBCode 지원)
    "WaitMessage",                  # 메시지 박스 + [Next] 버튼 대기
    "ShowDialog", "HideDialog",     # 명명된 다이얼로그 열기/닫기
    "Set",                          # Set LandLOD 0.5 등 변수 설정
    "HideAllDialogs",              # 모든 다이얼로그 닫기
    "HideAllToolbars",             # 모든 툴바 숨기기

    # ── Sound ──
    "PlaySound", "StopSound",       # 효과음 재생/중지
    "PlayMusic", "PauseMusic", "ResumeMusic",  # 음악 제어

    # ── Script Execution ──
    "Run",                   # Run "filename.se" (최대 16단계 중첩)

    # ── Utility ──
    "Screenshot",            # Screenshot / Screenshot { GUI true }
    "Log",                   # Log "message" (se.log에 기록)
}

# 금지 명령어 (SE 종료 방지)
BLOCKED_COMMANDS = {"Exit", "Quit"}

# ── SE 콘솔 Show/Hide용 이름 정규화 맵 (통합) ──────────────────────────────────
# SE 콘솔의 Show/Hide 명령은 복수형 이름을 요구하는 경우가 있음
OVERLAY_NAME_MAP = {
    # 단수 → 복수 변환
    "Atmosphere": "Atmospheres",
    "atmosphere": "Atmospheres",
    "atmospheres": "Atmospheres",
    "Orbit": "Orbits",
    "orbit": "Orbits",
    "orbits": "Orbits",
    "Label": "Labels",
    "label": "Labels",
    "labels": "Labels",
    "Constellation": "Constellations",
    "constellation": "Constellations",
    "constellations": "Constellations",
    "Grid": "Grids",
    "grid": "Grids",
    "grids": "Grids",
    "Marker": "Markers",
    "marker": "Markers",
    "markers": "Markers",
    "Cloud": "Clouds",
    "cloud": "Clouds",
    "clouds": "Clouds",
    "Nebula": "Nebulae",
    "nebula": "Nebulae",
    "nebulae": "Nebulae",
    "Eclipse": "Eclipses",
    "eclipse": "Eclipses",
    "eclipses": "Eclipses",
    "LensFlare": "LensFlares",
    "lensflare": "LensFlares",
    "lensflares": "LensFlares",
    "NightLight": "NightLights",
    "nightlight": "NightLights",
    "nightlights": "NightLights",
    "CometTail": "CometTails",
    "comettail": "CometTails",
    "comettails": "CometTails",
    "AccretionDisk": "AccretionDisks",
    "accretiondisk": "AccretionDisks",
    "accretiondisks": "AccretionDisks",
    "Jet": "Jets",
    "jet": "Jets",
    "jets": "Jets",
    # 이미 올바른 형태 (변환 불필요하지만 안전)
    "Atmospheres": "Atmospheres",
    "Orbits": "Orbits",
    "Labels": "Labels",
    "Constellations": "Constellations",
    "Grids": "Grids",
    "Markers": "Markers",
    "Clouds": "Clouds",
    "Water": "Water",
    "water": "Water",
    "Aurora": "Aurora",
    "aurora": "Aurora",
    "Nebulae": "Nebulae",
    "LensFlares": "LensFlares",
    "NightLights": "NightLights",
    "CometTails": "CometTails",
    "AccretionDisks": "AccretionDisks",
    "Jets": "Jets",
    "EclipseMask": "EclipseMask",
    "eclipsemask": "EclipseMask",
    "Vectors": "Vectors",
    "vectors": "Vectors",
    "SelPointer": "SelPointer",
    "VelVector": "VelVector",
    "OrbitMarks": "OrbitMarks",
    "orbitmarks": "OrbitMarks",
    "PlanetShine": "PlanetShine",
    "planetshine": "PlanetShine",
}


# ── SE 호환 천체 이름 매핑 ────────────────────────────────────────────────────
# SE 내부 카탈로그는 약칭(Proxima Cen)이나 바이어 명칭(Alpha Cen)을 사용한다.
# 흔히 사용되는 전체 이름을 SE가 인식하는 이름으로 변환.
_SE_NAME_ALIASES: dict[str, str] = {
    # 항성 — 전체 이름 → SE 약칭
    "proxima centauri":     "Proxima Cen",
    "alpha centauri":       "Alpha Cen",
    "alpha centauri a":     "Alpha Cen A",
    "alpha centauri b":     "Alpha Cen B",
    "alpha centauri c":     "Proxima Cen",
    "barnard's star":       "Barnard's Star",
    # 동반성 — SE 카탈로그에서 확인된 정확한 이름
    "sirius a":             "Sirius A",
    "sirius b":             "Sirius B",
    "procyon a":            "Procyon A",
    "procyon b":            "Procyon B",
    # 성운/은하 — 일반 이름 → 메시에/카탈로그 번호
    "andromeda galaxy":     "Andromeda",
    "orion nebula":         "M 42",
    "crab nebula":          "M 1",
    "ring nebula":          "M 57",
    "eagle nebula":         "M 16",
    "pillars of creation":  "M 16",
    "whirlpool galaxy":     "M 51",
    "sombrero galaxy":      "M 104",
    "triangulum galaxy":    "M 33",
    "pleiades":             "Melotte 22",
    "milky way":            "Milky Way",
    # 태양계 — 한국어 이름 지원
    "수성": "Mercury",
    "금성": "Venus",
    "지구": "Earth",
    "화성": "Mars",
    "목성": "Jupiter",
    "토성": "Saturn",
    "천왕성": "Uranus",
    "해왕성": "Neptune",
    "명왕성": "Pluto",
    "태양": "Sun",
    "달":   "Moon",
}


def resolve_object_name(name: str) -> str:
    """천체 이름을 SE 내부 카탈로그가 인식하는 이름으로 변환.
    매핑에 없으면 원래 이름을 그대로 반환한다.
    """
    return _SE_NAME_ALIASES.get(name.lower().strip(), name)


def sanitize_object_name(name: str) -> str:
    """천체 이름을 SE 호환으로 변환 + 위험 문자 제거."""
    name = resolve_object_name(name)
    for ch in ('"', '{', '}', '\n', '\r', '\\'):
        name = name.replace(ch, '')
    return name.strip()[:100]


def normalize_overlay_name(name: str) -> str:
    """오버레이 이름을 SE 콘솔이 요구하는 정확한 형태로 정규화"""
    return OVERLAY_NAME_MAP.get(name, name)


def validate_commands(commands: list[str]) -> list[str]:
    """명령어 화이트리스트 검사. 허용되지 않은 명령어 반환."""
    blocked = []
    for cmd in commands:
        stripped = cmd.strip()
        if not stripped or stripped.startswith("//"):
            continue  # 빈 줄·주석은 검사 제외
        keyword = stripped.split()[0]
        if keyword in BLOCKED_COMMANDS:
            blocked.append(cmd)
        elif keyword not in ALLOWED_COMMANDS:
            blocked.append(cmd)
    return blocked


class ScriptBridge:
    """SpaceEngine .se 스크립트 생성 및 실행 브릿지"""

    def __init__(self, config: SpaceEngineConfig, templates_dir: str = "templates"):
        self.config = config
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_script(self, commands: list[str], filename: str | None = None) -> Path:
        """SE 명령어 리스트로 .se 스크립트 파일 생성"""
        blocked = validate_commands(commands)
        if blocked:
            raise ValueError(f"허용되지 않은 명령어 포함: {blocked}")

        if filename is None:
            filename = f"mcp_{int(time.time())}.se"

        script_path = self.config.scripts_dir / filename
        content = "\n".join(commands)
        script_path.write_text(content, encoding="utf-8-sig")
        return script_path

    def generate_from_template(self, template_name: str, context: dict) -> Path:
        """Jinja2 템플릿으로 .se 스크립트 생성"""
        template = self.jinja_env.get_template(template_name)
        rendered = template.render(**context)
        filename = f"mcp_{template_name.replace('.j2', '')}"
        script_path = self.config.scripts_dir / filename
        script_path.write_text(rendered, encoding="utf-8-sig")
        return script_path

    async def execute_script(self, script_path: Path, timeout: float = 10.0, *, use_run: bool = False) -> dict:
        """
        .se 스크립트를 SpaceEngine에 전달하여 실행.

        기본 모드 (use_run=False):
            스크립트 파일의 명령어를 읽어 콘솔에 줄 단위로 직접 전송합니다.
            SE 콘솔이 각 명령을 즉시 실행하므로 경로 문제가 발생하지 않습니다.

        Run 모드 (use_run=True):
            SE 콘솔에서 'Run "mcp/파일명"' 명령으로 스크립트 파일 자체를 실행합니다.
            멀티라인 블록이 포함된 복잡한 스크립트(스플라인 등)에 적합합니다.
        """
        if not script_path.exists():
            return {"status": "error", "message": f"스크립트 파일을 찾을 수 없음: {script_path}"}

        # se.log 피드백: 명령 전송 전 로그 위치 기록
        log_pos_before = 0
        log_path = self.config.log_file
        if log_path.exists():
            try:
                log_pos_before = len(log_path.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                pass

        if use_run:
            # Run 모드: SE가 파일을 직접 파싱/실행
            relative_name = script_path.name
            run_command = f'Run "mcp/{relative_name}"'
            result = send_commands_via_console([run_command])
        else:
            # 직접 전송 모드: 파일 내용을 읽어 줄 단위로 콘솔에 전송
            content = script_path.read_text(encoding="utf-8")
            lines = [l.strip() for l in content.splitlines()
                     if l.strip() and not l.strip().startswith("//")]
            if not lines:
                return {"status": "error", "message": "스크립트에 실행할 명령어가 없음"}
            result = send_commands_via_console(lines)

        result["script_path"] = str(script_path)

        # se.log 피드백: 명령 전송 후 새 로그 검사 (에러/경고 감지)
        if log_path.exists():
            try:
                from spaceengine_mcp.bridges.log_bridge import get_incremental_entries
                import time as _time
                _time.sleep(0.3)  # SE가 로그를 기록할 시간 확보
                new_entries, _ = get_incremental_entries(log_path, log_pos_before)
                errors = [e["message"] for e in new_entries if e.get("level") == "error"]
                warnings = [e["message"] for e in new_entries if e.get("level") == "warning"]
                if errors:
                    result["se_errors"] = errors[:5]
                if warnings:
                    result["se_warnings"] = warnings[:5]
            except Exception:
                pass  # 로그 파싱 실패는 무시 (명령 실행 자체는 성공)

        return result

    # 메인 메뉴 카메라 잠금을 해제하는 명령어 시퀀스
    UNLOCK_COMMANDS = [
        'UserMoveControl "Free"',
        'UserRotationControl "Free"',
        'UserTimeControl "Free"',
    ]

    def build_navigation_commands(
        self, target: str, mode: str = "goto", distance_rad: float = 3.0, transition_time: float = 5.0
    ) -> list[str]:
        """천체 탐색 명령어 시퀀스 생성 (공식 문서 기준)"""
        safe_target = sanitize_object_name(target)
        # 메인 메뉴 카메라 잠금 해제 (Scene1.se가 UserMoveControl "Disabled" 설정)
        commands = list(self.UNLOCK_COMMANDS)
        commands.append(f'Select "{safe_target}"')
        if mode == "goto":
            commands.append(f'Goto {{ Time {transition_time} DistRad {distance_rad} }}')
            commands.append(f'Wait {transition_time + 1}')
        elif mode == "center":
            commands.append(f'Center {{ Time {transition_time} }}')
        elif mode == "follow":
            commands.append('Follow')
        return commands

    def build_time_commands(self, date_iso: str | None = None, rate: float | None = None) -> list[str]:
        """시간 제어 명령어 생성 (공식: Date, TimeScale, StopTime, StartTime)"""
        commands = []
        if date_iso:
            # ISO 8601 → SE 형식 변환 (2024-04-08T18:00:00 → "2024.04.08 18:00:00")
            try:
                date_part, time_part = date_iso.split("T") if "T" in date_iso else (date_iso, "00:00:00")
                se_date = date_part.replace("-", ".")
                commands.append(f'Date "{se_date} {time_part}"')
            except ValueError:
                raise ValueError(f"날짜 형식 오류 (ISO 8601 필요): {date_iso}")
        if rate is not None:
            if rate == 0:
                commands.append("StopTime")
            elif rate == 1:
                commands.append("StartTime")
            else:
                commands.append(f"TimeScale {rate}")
        return commands

    def build_overlay_commands(self, overlay: str, visible: bool) -> list[str]:
        """오버레이 표시/숨김 명령어 생성"""
        action = "Show" if visible else "Hide"
        # SE 콘솔이 요구하는 정확한 이름으로 변환 (통합 맵 사용)
        overlay = normalize_overlay_name(overlay)
        return [f"{action} {overlay}"]

    def build_camera_commands(
        self,
        dist: float | None = None,
        dist_rad: float | None = None,
        fov: float | None = None,
        time: float = 3.0,
    ) -> list[str]:
        """카메라 파라미터 조정 명령어 생성 (공식: Goto + FOV)"""
        commands = []
        # 거리 조정 → Goto 명령 사용 (현재 선택된 천체 기준)
        if dist is not None or dist_rad is not None:
            params = [f"Time {time}"]
            if dist is not None:
                params.append(f"DistKm {dist}")
            if dist_rad is not None:
                params.append(f"DistRad {dist_rad}")
            commands.append(f'Goto {{ {" ".join(params)} }}')
            commands.append(f"Wait {time + 1}")
        # FOV → 독립 명령 (즉시 적용)
        if fov is not None:
            commands.append(f"FOV {fov}")
        return commands

    def build_sound_commands(
        self,
        action: str,
        filename: str | None = None,
        volume: float | None = None,
    ) -> list[str]:
        """사운드 제어 명령어 생성"""
        commands = []
        if action == "play" and filename:
            safe_name = sanitize_object_name(filename)
            cmd = f'PlaySound "{safe_name}"'
            if volume is not None:
                cmd = f'PlaySound {{ File "{safe_name}" Volume {volume} }}'
            commands.append(cmd)
        elif action == "stop":
            commands.append("StopSound")
        elif action == "play_music" and filename:
            safe_name = sanitize_object_name(filename)
            commands.append(f'PlayMusic "{safe_name}"')
        elif action == "stop_music":
            commands.append("PauseMusic")  # 공식 문서: StopMusic 없음, PauseMusic 사용
        return commands

    def build_message_commands(
        self,
        text: str,
        duration: float = 5.0,
        show: bool = True,
    ) -> list[str]:
        """화면 메시지 표시/숨김 명령어 생성 (공식: Print / HidePrint)"""
        if not show:
            return ["HidePrint"]
        safe_text = text.replace('"', "'")
        return [f'Print "{safe_text}" {{ Time {duration} }}']

    def build_screenshot_command(self) -> list[str]:
        """스크린샷 캡처 명령어 생성 (WaitTrigger로 저장 완료 대기)"""
        return ["Screenshot", 'WaitTrigger "ScreenshotComplete"']

    def build_gui_commands(self, visible: bool) -> list[str]:
        """UI 표시/숨김 명령어 생성 (SE에는 ShowGUI 변수가 없음).
        숨김: HideAllDialogs + HideAllToolbars
        복원: SE가 RestoreVars 시 자동 복원하므로 별도 명령 불필요.
        """
        if not visible:
            return ["HideAllDialogs", "HideAllToolbars"]
        return []  # SE에 ShowAll 명령 없음 — RestoreVars 또는 사용자 수동 복원

    def build_follow_commands(self, target: str, mode: str = "follow") -> list[str]:
        """추적 모드 명령어 생성 (공식: Follow/Track은 인자 없음, Free로 해제)"""
        safe_target = sanitize_object_name(target)
        if mode == "unfollow":
            return ["Free"]  # 카메라 바인딩 해제
        elif mode == "untrack":
            return ["Untrack"]
        elif mode == "track":
            return [f'Select "{safe_target}"', "Track"]
        else:  # follow
            return [f'Select "{safe_target}"', "Follow"]

    # ── Phase 5 build 메서드 ──────────────────────────────────────────────────

    def build_variable_commands(
        self, variable: str, action: str = "set", value: str | None = None,
    ) -> list[str]:
        """SE 변수 제어 명령어 생성 (Set/SetForce/SetU/Reset)"""
        safe_var = sanitize_object_name(variable)
        if action == "reset":
            return [f"Reset {safe_var}"]
        if value is None:
            raise ValueError(f"action='{action}'에는 value가 필요합니다.")
        safe_val = value.replace('"', '').replace('{', '').replace('}', '').strip()
        if action == "set":
            return [f"Set {safe_var} {safe_val}"]
        elif action == "set_force":
            return [f"SetForce {safe_var} {safe_val}"]
        elif action == "set_u":
            return [f"SetU {safe_var} {safe_val}"]
        else:
            raise ValueError(f"지원하지 않는 action: {action}")

    def build_interpolate_commands(
        self, variable: str, target_value: float,
        duration: float = 5.0, function: str = "linear",
    ) -> list[str]:
        """변수 보간 애니메이션 명령어 생성 (Interpolate)

        유효한 function 값: linear, quadric, cubic, sin, exp, revexp
        """
        safe_var = sanitize_object_name(variable)
        return [f'Interpolate {safe_var} {{ To {target_value} Time {duration} Func "{function}" }}']

    def build_spline_path_commands(
        self, name: str, knots: list[dict],
        auto_play: bool = True, play_time: float = 30.0,
    ) -> list[str]:
        """스플라인 카메라 경로 정의 + 재생 명령어 생성"""
        safe_name = sanitize_object_name(name)
        commands = list(self.UNLOCK_COMMANDS)
        knot_lines = []
        for knot in knots:
            parts = []
            if knot.get("select"):
                parts.append(f'Select "{sanitize_object_name(knot["select"])}"')
            if knot.get("goto_params"):
                safe_params = knot["goto_params"].replace('"', '').replace('\\', '')
                parts.append(f"Goto {{ {safe_params} }}")
            if knot.get("fov") is not None:
                parts.append(f"FOV {knot['fov']}")
            if knot.get("wait") is not None:
                parts.append(f"Wait {knot['wait']}")
            knot_lines.append("    Knot { " + " ".join(parts) + " }")
        commands.append(f'SplinePath "{safe_name}"')
        commands.append("{")
        commands.extend(knot_lines)
        commands.append("}")
        if auto_play:
            commands.append(f'PlaySplinePath "{safe_name}" {{ Time {play_time} }}')
            commands.append(f"Wait {int(play_time) + 1}")
        return commands

    def build_waypoint_commands(self, name: str = "", mode: str = "create") -> list[str]:
        """웨이포인트 관리 명령어 생성"""
        if mode == "clear_all":
            return ["ClearWaypoints"]
        safe_name = sanitize_object_name(name)
        if mode == "create":
            return [f'Waypoint "{safe_name}"']
        elif mode == "delete":
            return [f'DeleteWaypoint "{safe_name}"']
        elif mode == "goto":
            return [f'GotoWaypoint "{safe_name}"']
        else:
            raise ValueError(f"지원하지 않는 mode: {mode}")

    def build_flight_commands(
        self, action: str = "fly", x: float = 0, y: float = 0, z: float = 0,
    ) -> list[str]:
        """카메라 자유 비행 명령어 생성 (Fly/Turn/Orbit)"""
        if action == "fly":
            return [f"Fly {x} {y} {z}"]
        elif action == "turn":
            return [f"Turn {x} {y} {z}"]
        elif action == "orbit":
            return [f"Orbit {x} {y} {z}"]
        elif action == "stop_fly":
            return ["StopFly"]
        elif action == "stop_turn":
            return ["StopTurn"]
        elif action == "stop_orbit":
            return ["StopOrbit"]
        else:
            raise ValueError(f"지원하지 않는 action: {action}")

    def build_speed_commands(self, speed: float, unit: str = "internal") -> list[str]:
        """이동 속도 설정 명령어 생성"""
        if unit == "km":
            return [f"SpeedKm {speed}"]
        return [f"Speed {speed}"]

    def build_fade_commands(self, action: str = "fade_out", duration: float = 1.0) -> list[str]:
        """화면 페이드 효과 명령어 생성"""
        if action == "fade_out":
            return [f"FadeOut {{ Time {duration} }}"]
        elif action == "fade_in":
            return [f"FadeIn {{ Time {duration} }}"]
        else:
            raise ValueError(f"지원하지 않는 action: {action}")

    def build_dialog_commands(self, dialog_name: str = "", action: str = "show") -> list[str]:
        """다이얼로그 관리 명령어 생성"""
        if action == "hide_all":
            return ["HideAllDialogs"]
        safe_name = sanitize_object_name(dialog_name)
        if action == "show":
            return [f'ShowDialog "{safe_name}"']
        elif action == "hide":
            return [f'HideDialog "{safe_name}"']
        else:
            raise ValueError(f"지원하지 않는 action: {action}")

    def build_advanced_message_commands(
        self, text: str, wait_for_input: bool = False, duration: float = 5.0,
    ) -> list[str]:
        """고급 메시지 명령어 생성 (ShowMessage/WaitMessage — BBCode 지원)"""
        safe_text = text.replace('"', "'")
        if wait_for_input:
            return [f'WaitMessage "{safe_text}"']
        return [f'ShowMessage "{safe_text}"', f"Wait {duration}", "HideMessage"]

    # ── 성능 프리셋 ──────────────────────────────────────────────────────────

    # SE 공식 변수 기반 5단계 프리셋 (CLAUDE.md + SE_SCRIPT_REFERENCE 참조)
    PERFORMANCE_PRESETS: dict[str, dict[str, str]] = {
        "potato": {
            "QualityPreset": "0",
            "LandLOD": "-1",
            "LandLODmaxRes": "480",
            "FBOResolution": "0.1",
            "MSAALevel": "0",
            "FXAA": "false",
            "AnisotropyLevel": "0",
            "BloomBright": "0",
            "MaxTilesPerFrame": "1",
            "MaxTimePerFrame": "2",
            "DrawClouds": "false",
            "DrawWater": "false",
            "AuroraQuality": "0",
            "BlackHoleQuality": "0",
            "VSync": "0",
        },
        "low": {
            "QualityPreset": "1",
            "LandLOD": "-0.5",
            "LandLODmaxRes": "720",
            "FBOResolution": "0.2",
            "MSAALevel": "0",
            "FXAA": "true",
            "AnisotropyLevel": "2",
            "BloomBright": "0.3",
            "MaxTilesPerFrame": "3",
            "MaxTimePerFrame": "4",
            "DrawClouds": "false",
            "DrawWater": "true",
            "AuroraQuality": "0",
            "BlackHoleQuality": "1",
            "VSync": "1",
        },
        "balanced": {
            "QualityPreset": "2",
            "LandLOD": "0",
            "LandLODmaxRes": "1080",
            "FBOResolution": "0.35",
            "MSAALevel": "0",
            "FXAA": "true",
            "AnisotropyLevel": "4",
            "BloomBright": "0.5",
            "MaxTilesPerFrame": "5",
            "MaxTimePerFrame": "6",
            "DrawClouds": "true",
            "DrawWater": "true",
            "AuroraQuality": "0",
            "BlackHoleQuality": "2",
            "VSync": "2",
        },
        "high": {
            "QualityPreset": "3",
            "LandLOD": "0.5",
            "LandLODmaxRes": "2160",
            "FBOResolution": "0.5",
            "MSAALevel": "4",
            "FXAA": "true",
            "AnisotropyLevel": "8",
            "BloomBright": "0.7",
            "MaxTilesPerFrame": "8",
            "MaxTimePerFrame": "8",
            "DrawClouds": "true",
            "DrawWater": "true",
            "AuroraQuality": "1",
            "BlackHoleQuality": "2",
            "VSync": "2",
        },
        "ultra": {
            "QualityPreset": "4",
            "LandLOD": "1",
            "LandLODmaxRes": "4320",
            "FBOResolution": "1.0",
            "MSAALevel": "8",
            "FXAA": "true",
            "AnisotropyLevel": "16",
            "BloomBright": "0.7",
            "MaxTilesPerFrame": "15",
            "MaxTimePerFrame": "15",
            "DrawClouds": "true",
            "DrawWater": "true",
            "AuroraQuality": "1",
            "BlackHoleQuality": "3",
            "VSync": "2",
        },
    }

    def build_performance_commands(self, preset: str) -> list[str]:
        """성능 프리셋 명령어 생성 (SaveVars → SetForce 다수 → 메시지)"""
        if preset not in self.PERFORMANCE_PRESETS:
            raise ValueError(f"알 수 없는 프리셋: {preset}. 사용 가능: {list(self.PERFORMANCE_PRESETS.keys())}")

        settings = self.PERFORMANCE_PRESETS[preset]
        commands = ["SaveVars"]  # 현재 설정 백업
        for var_name, value in settings.items():
            commands.append(f"SetForce {var_name} {value}")
        commands.append(f'Print "Performance: {preset}" {{ Time 3 }}')
        return commands

    def build_restore_defaults_commands(self) -> list[str]:
        """모든 변경 설정을 기본값으로 복원"""
        commands = ["RestoreVars"]
        # 주요 변수를 명시적으로 Reset
        for var_name in [
            "QualityPreset", "LandLOD", "LandLODmaxRes", "FBOResolution",
            "MSAALevel", "FXAA", "AnisotropyLevel", "BloomBright",
            "MaxTilesPerFrame", "MaxTimePerFrame", "DrawClouds", "DrawWater",
            "AuroraQuality", "BlackHoleQuality", "VSync",
        ]:
            commands.append(f"Reset {var_name}")
        commands.append('Print "Settings restored to defaults" { Time 3 }')
        return commands
