"""Phase 11 Tools — 복합 워크플로 도구

cinematic_sequence, apply_preset, get_object_info, timelapse_capture, save_scene, load_scene, list_scenes
"""

import json
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from spaceengine_mcp.bridges.script_bridge import sanitize_object_name

try:
    from spaceengine_mcp.bridges.console_bridge import send_commands_via_console
except ImportError:
    def send_commands_via_console(commands, close_console=True):
        return {"status": "error", "message": "pywin32 not available"}


# ── 모델 ──────────────────────────────────────────────────────────────────────

class CinematicStep(BaseModel):
    """시네마틱 시퀀스의 단일 스텝"""
    action: Literal[
        "navigate", "fade_out", "fade_in", "message", "wait",
        "follow", "unfollow", "hide_gui", "show_gui",
        "set_fov", "overlay_on", "overlay_off",
        "flyby", "screenshot", "start_record", "stop_record",
        "set_time", "time_rate",
    ] = Field(description="수행할 동작")
    target: str | None = Field(None, description="천체 이름 (navigate/follow/flyby용)")
    text: str | None = Field(None, description="메시지 텍스트 (message용)")
    value: float | None = Field(None, description="수치 값 (wait=초, set_fov=도, fade=초, time_rate=배속)")
    overlay: str | None = Field(None, description="오버레이 이름 (overlay_on/off용)")
    distance_rad: float | None = Field(None, description="관측 거리 (navigate/flyby용)")
    transition_time: float | None = Field(None, description="전환 시간 (navigate용)")
    date: str | None = Field(None, description="날짜 ISO 8601 (set_time용)")


# ── 프리셋 정의 ──────────────────────────────────────────────────────────────

PRESETS = {
    "cinematic_dark": {
        "description": "시네마틱 촬영용 (UI 숨김, 깨끗한 화면)",
        "gui": False,
        "commands": [
            "Hide Labels",
            "Hide Orbits",
            "Hide Constellations",
            "Hide Markers",
            "FOV 30",
        ],
    },
    "cinematic_wide": {
        "description": "시네마틱 광각 (UI 숨김, 넓은 시야)",
        "gui": False,
        "commands": [
            "Hide Labels",
            "Hide Orbits",
            "Hide Constellations",
            "FOV 90",
        ],
    },
    "educational": {
        "description": "교육/학습용 (라벨, 궤도, 별자리 표시)",
        "gui": True,
        "commands": [
            "Show Labels",
            "Show Orbits",
            "Show Constellations",
            "FOV 45",
        ],
    },
    "observation": {
        "description": "천체 관측용 (라벨만 표시, 깔끔)",
        "gui": True,
        "commands": [
            "Show Labels",
            "Hide Orbits",
            "Hide Constellations",
            "Hide Markers",
            "FOV 45",
        ],
    },
    "screenshot": {
        "description": "고품질 스크린샷용 (UI 숨김, 표준 FOV)",
        "gui": False,
        "commands": [
            "Hide Labels",
            "Hide Orbits",
            "Hide Constellations",
            "Hide Markers",
            "FOV 45",
        ],
    },
    "default": {
        "description": "기본 설정 복원",
        "gui": True,
        "commands": [
            "Show Labels",
            "Hide Orbits",
            "Hide Constellations",
            "Hide Markers",
            "FOV 45",
        ],
    },
}


def register_tools(mcp, script_bridge, state_bridge, config):

    # ── 1. cinematic_sequence ─────────────────────────────────────────────

    @mcp.tool()
    async def cinematic_sequence(
        steps: list[dict],
        auto_hide_gui: bool = True,
    ) -> dict:
        """
        시네마틱 시퀀스를 한 번에 실행합니다.
        여러 동작(이동, 페이드, 메시지, 스크린샷 등)을 배열로 전달하면
        하나의 SE 스크립트로 합쳐서 순차 실행합니다.

        Args:
            steps: 실행할 동작 목록 (순서대로 실행)
            auto_hide_gui: True이면 시퀀스 시작 시 GUI 자동 숨김, 종료 시 복원
        """
        commands = list(script_bridge.UNLOCK_COMMANDS)

        # GUI 숨기기 (HideAllDialogs/HideAllToolbars — SE에 ShowGUI 변수 없음)
        if auto_hide_gui:
            send_commands_via_console(["HideAllDialogs", "HideAllToolbars"])

        for step in steps:
            # dict → CinematicStep 변환 (HTTP API 경유 시 dict로 올 수 있음)
            if isinstance(step, dict):
                step = CinematicStep(**step)
            step_cmds = _build_step_commands(script_bridge, step)
            commands.extend(step_cmds)

        script_path = script_bridge.generate_script(commands, filename="mcp_cinematic.se")
        result = await script_bridge.execute_script(script_path, use_run=True)

        if auto_hide_gui:
            pass  # SE에 ShowAll 명령 없음 — 사용자가 수동 복원

        result["steps_count"] = len(steps)
        return result

    # ── 2. apply_preset ───────────────────────────────────────────────────

    @mcp.tool()
    async def apply_preset(
        preset: Literal[
            "cinematic_dark", "cinematic_wide", "educational",
            "observation", "screenshot", "default",
        ],
    ) -> dict:
        """
        분위기/용도별 프리셋을 한 번에 적용합니다.
        GUI, 오버레이, FOV 등을 목적에 맞게 일괄 설정합니다.

        Args:
            preset: 프리셋 이름
                - cinematic_dark: 시네마틱 촬영 (UI 숨김, FOV 30)
                - cinematic_wide: 시네마틱 광각 (UI 숨김, FOV 90)
                - educational: 교육용 (라벨+궤도+별자리 표시)
                - observation: 관측용 (라벨만 표시)
                - screenshot: 스크린샷용 (UI 숨김, FOV 45)
                - default: 기본 설정 복원
        """
        preset_data = PRESETS[preset]
        commands = list(preset_data["commands"])
        script_path = script_bridge.generate_script(commands, filename="mcp_preset.se")
        result = await script_bridge.execute_script(script_path, use_run=True)

        # GUI 숨기기/복원 (SE에 ShowGUI 변수 없음)
        gui_visible = preset_data.get("gui")
        if gui_visible is not None and not gui_visible:
            send_commands_via_console(["HideAllDialogs", "HideAllToolbars"])

        result["preset"] = preset
        result["description"] = preset_data["description"]
        return result

    # ── 3. get_object_info ────────────────────────────────────────────────

    @mcp.tool()
    def get_object_info(target: str | None = None) -> dict:
        """
        천체의 상세 정보를 구조화된 데이터로 반환합니다.
        SE 로그에서 선택된 천체 정보를 파싱하고,
        카탈로그에서 추가 데이터를 검색합니다.

        Args:
            target: 천체 이름 (None이면 현재 선택된 천체)
        """
        from spaceengine_mcp.bridges.log_bridge import (
            get_selected_object,
            get_camera_info,
            parse_log_tail,
        )

        log_path = config.log_file
        result: dict[str, Any] = {"status": "ok"}

        # 현재 선택된 천체
        selected = get_selected_object(log_path)
        if target:
            result["queried"] = target
        result["selected_object"] = selected

        # 카메라 정보
        camera = get_camera_info(log_path)
        result["camera"] = camera

        # 로그에서 천체 관련 정보 추출
        search_name = target or selected
        if search_name:
            entries = parse_log_tail(log_path, lines=500)
            object_info = _extract_object_info_from_log(entries, search_name)
            result["object_data"] = object_info

        # 카탈로그에서 검색 시도
        if search_name:
            try:
                from spaceengine_mcp.bridges.catalog_bridge import CatalogBridge
                cat_bridge = CatalogBridge(config)
                cat_results = cat_bridge.search_catalogs(search_name)
                if cat_results:
                    result["catalog_data"] = cat_results[:3]
            except Exception:
                pass

        return result

    # ── 4. timelapse_capture ──────────────────────────────────────────────

    @mcp.tool()
    async def timelapse_capture(
        target: str,
        time_rate: float = 10000.0,
        duration: float = 10.0,
        hide_gui: bool = True,
    ) -> dict:
        """
        타임랩스 장면을 자동 설정합니다.
        천체를 추적하며 시간을 가속하고, 지정 시간 후 정상으로 복원합니다.
        비디오 녹화(F9)와 함께 사용하면 타임랩스 영상이 됩니다.

        Args:
            target: 추적할 천체 이름
            time_rate: 시간 가속 배율 (기본 10000x)
            duration: 촬영 시간 — 실제 초 단위 (기본 10초)
            hide_gui: UI 숨김 여부
        """
        safe_target = sanitize_object_name(target)
        commands = list(script_bridge.UNLOCK_COMMANDS)

        # 1) 천체 선택 + 추적
        commands.append(f'Select "{safe_target}"')
        commands.append("Follow")

        # 2) UI 숨기기 (SE에 ShowGUI 변수 없음 → HideAllDialogs/HideAllToolbars)
        if hide_gui:
            send_commands_via_console(["HideAllDialogs", "HideAllToolbars"])
            commands.append("Hide Labels")

        # 3) 시간 가속
        commands.append(f"TimeScale {time_rate}")

        # 4) 촬영 시간만큼 대기
        commands.append(f"Wait {duration}")

        # 5) 복원
        commands.append("TimeScale 1")
        commands.append("StartTime")
        commands.append("Free")

        script_path = script_bridge.generate_script(commands, filename="mcp_timelapse.se")
        result = await script_bridge.execute_script(script_path, use_run=True)

        result["target"] = target
        result["time_rate"] = time_rate
        result["duration_seconds"] = duration
        result["tip"] = "F9 키로 비디오 녹화를 시작/정지할 수 있습니다"
        return result

    # ── 5. save_scene / load_scene / list_scenes ──────────────────────────

    scenes_dir = Path(config.install_path) / "data" / "scripts" / "mcp" / "scenes"

    @mcp.tool()
    async def save_scene(
        name: str,
        description: str = "",
    ) -> dict:
        """
        현재 SE 장면(카메라 위치, 시간, 설정)을 이름 붙여 저장합니다.
        여러 장면을 저장해두고 나중에 load_scene으로 복원할 수 있습니다.

        Args:
            name: 장면 이름 (예: "earth_sunrise", "saturn_rings")
            description: 장면 설명
        """
        from spaceengine_mcp.bridges.log_bridge import (
            get_selected_object,
            get_camera_info,
        )

        log_path = config.log_file
        safe_name = sanitize_object_name(name).replace(" ", "_")

        # 현재 상태 수집
        selected = get_selected_object(log_path)
        camera = get_camera_info(log_path)

        scene_data = {
            "name": safe_name,
            "description": description,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "selected_object": selected,
            "camera": camera,
        }

        # SaveVars 실행 (SE 내부 상태 저장)
        save_commands = ["SaveVars"]
        script_path = script_bridge.generate_script(save_commands, filename=f"mcp_save_{safe_name}.se")
        await script_bridge.execute_script(script_path)

        # JSON 파일로 장면 메타데이터 저장
        scenes_dir.mkdir(parents=True, exist_ok=True)
        scene_file = scenes_dir / f"{safe_name}.json"
        scene_file.write_text(
            json.dumps(scene_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "status": "saved",
            "scene": safe_name,
            "file": str(scene_file),
            "selected_object": selected,
            "description": description,
        }

    @mcp.tool()
    async def load_scene(name: str) -> dict:
        """
        save_scene으로 저장한 장면을 복원합니다.
        저장된 천체로 이동하고 카메라 상태를 복원합니다.

        Args:
            name: 장면 이름
        """
        safe_name = sanitize_object_name(name).replace(" ", "_")
        scene_file = scenes_dir / f"{safe_name}.json"

        if not scene_file.exists():
            available = [f.stem for f in scenes_dir.glob("*.json")] if scenes_dir.exists() else []
            return {
                "status": "error",
                "message": f"장면 '{safe_name}'을 찾을 수 없습니다",
                "available_scenes": available,
            }

        scene_data = json.loads(scene_file.read_text(encoding="utf-8"))

        # 복원 명령어 생성
        commands = list(script_bridge.UNLOCK_COMMANDS)

        # RestoreVars (SE 내부 상태 복원)
        commands.append("RestoreVars")

        # 선택된 천체로 이동
        selected = scene_data.get("selected_object")
        if selected:
            commands.append(f'Select "{sanitize_object_name(selected)}"')
            commands.append("Goto { Time 3 DistRad 3 }")
            commands.append("Wait 4")

        script_path = script_bridge.generate_script(commands, filename=f"mcp_load_{safe_name}.se")
        result = await script_bridge.execute_script(script_path)
        result["scene"] = scene_data
        return result

    # ── 6. set_performance ─────────────────────────────────────────────

    @mcp.tool()
    async def set_performance(
        preset: Literal["potato", "low", "balanced", "high", "ultra"] = "balanced",
    ) -> dict:
        """
        SpaceEngine 그래픽 성능을 자연어 프리셋으로 조정합니다.
        사양이 낮은 컴퓨터에서는 'potato'나 'low'를 사용하세요.

        Args:
            preset: 성능 프리셋
                - potato: 최저 사양 (구름/물 OFF, 최소 LOD, AA OFF)
                - low: 저사양 (구름 OFF, 낮은 LOD, FXAA만)
                - balanced: 균형 (기본값 수준)
                - high: 고사양 (MSAA 4x, 높은 LOD)
                - ultra: 최고 사양 (MSAA 8x, 최대 LOD, 모든 효과)
        """
        try:
            commands = script_bridge.build_performance_commands(preset)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        script_path = script_bridge.generate_script(commands, filename=f"mcp_perf_{preset}.se")
        result = await script_bridge.execute_script(script_path, use_run=True)
        result["preset"] = preset
        result["description"] = {
            "potato": "최저 사양 — 구름/물 OFF, 모든 효과 최소화",
            "low": "저사양 — 기본 렌더링만, 부드러운 프레임",
            "balanced": "균형 — 시각 효과와 성능의 적절한 타협",
            "high": "고사양 — 대부분의 효과 활성화, MSAA 4x",
            "ultra": "최고 사양 — 모든 효과 최대, MSAA 8x",
        }[preset]
        return result

    # ── 7. restore_defaults ──────────────────────────────────────────

    @mcp.tool()
    async def restore_defaults() -> dict:
        """
        모든 변경된 설정을 SpaceEngine 기본값으로 복원합니다.
        set_performance, apply_preset 등으로 변경한 설정을 되돌립니다.
        """
        commands = script_bridge.build_restore_defaults_commands()
        script_path = script_bridge.generate_script(commands, filename="mcp_restore_defaults.se")
        return await script_bridge.execute_script(script_path, use_run=True)

    @mcp.tool()
    def list_scenes() -> dict:
        """
        저장된 모든 장면 목록을 반환합니다.
        """
        if not scenes_dir.exists():
            return {"status": "ok", "scenes": [], "count": 0}

        scenes = []
        for f in sorted(scenes_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                scenes.append({
                    "name": data.get("name", f.stem),
                    "description": data.get("description", ""),
                    "created_at": data.get("created_at", ""),
                    "selected_object": data.get("selected_object", ""),
                })
            except (json.JSONDecodeError, OSError):
                scenes.append({"name": f.stem, "description": "(읽기 오류)", "created_at": ""})

        return {"status": "ok", "scenes": scenes, "count": len(scenes)}


# ── 헬퍼 함수 ────────────────────────────────────────────────────────────────

def _build_step_commands(script_bridge, step: CinematicStep) -> list[str]:
    """CinematicStep → SE 명령어 리스트 변환"""
    action = step.action
    commands = []

    if action == "navigate":
        target = step.target or "Earth"
        dist = step.distance_rad or 3.0
        trans = step.transition_time or 5.0
        commands = script_bridge.build_navigation_commands(
            target=target, mode="goto", distance_rad=dist, transition_time=trans,
        )
        # UNLOCK은 시퀀스 시작에서 이미 처리하므로 제거
        commands = [c for c in commands if "UserMoveControl" not in c
                    and "UserRotationControl" not in c
                    and "UserTimeControl" not in c]

    elif action == "fade_out":
        dur = step.value or 1.0
        commands = script_bridge.build_fade_commands("fade_out", dur)

    elif action == "fade_in":
        dur = step.value or 1.0
        commands = script_bridge.build_fade_commands("fade_in", dur)

    elif action == "message":
        text = step.text or ""
        dur = step.value or 5.0
        commands = script_bridge.build_message_commands(text, duration=dur)

    elif action == "wait":
        dur = step.value or 3.0
        commands = [f"Wait {dur}"]

    elif action == "follow":
        target = step.target or "Earth"
        commands = script_bridge.build_follow_commands(target, "follow")

    elif action == "unfollow":
        commands = ["Free"]

    elif action == "hide_gui":
        # SE에 ShowGUI 변수 없음 → HideAllDialogs/HideAllToolbars 사용
        send_commands_via_console(["HideAllDialogs", "HideAllToolbars"])
        commands = []

    elif action == "show_gui":
        # SE에 ShowAll 명령 없음 — no-op (사용자 수동 복원)
        commands = []

    elif action == "set_fov":
        fov = step.value or 45.0
        commands = [f"FOV {fov}"]

    elif action == "overlay_on":
        overlay = step.overlay or "Labels"
        commands = script_bridge.build_overlay_commands(overlay, True)

    elif action == "overlay_off":
        overlay = step.overlay or "Labels"
        commands = script_bridge.build_overlay_commands(overlay, False)

    elif action == "flyby":
        target = step.target or "Earth"
        dist = step.distance_rad or 10.0
        safe = sanitize_object_name(target)
        commands = [
            f'Select "{safe}"',
            f"Goto {{ Time 5 DistRad {dist} }}",
            "Wait 5",
            f"Goto {{ Time 15 DistRad 2.0 }}",
            "Wait 15",
        ]

    elif action == "screenshot":
        commands = script_bridge.build_screenshot_command()

    elif action == "start_record":
        # 녹화는 키보드 시뮬레이션으로 처리 (F9)
        commands = ['Log "MCP: Recording started"']

    elif action == "stop_record":
        commands = ['Log "MCP: Recording stopped"']

    elif action == "set_time":
        date = step.date or "2024-01-01T12:00:00"
        commands = script_bridge.build_time_commands(date_iso=date)

    elif action == "time_rate":
        rate = step.value or 1.0
        commands = script_bridge.build_time_commands(rate=rate)

    return commands


def _extract_object_info_from_log(entries: list[dict], object_name: str) -> dict:
    """SE 로그 엔트리에서 천체 관련 정보를 추출"""
    info = {}
    name_lower = object_name.lower()

    for entry in entries:
        msg = entry.get("message", "")
        msg_lower = msg.lower()

        if name_lower not in msg_lower:
            continue

        # Selected object 정보
        if "selected" in msg_lower or "select" in msg_lower:
            info["last_selected"] = msg.strip()

        # 거리 정보
        if "dist" in msg_lower or "distance" in msg_lower:
            info["distance_info"] = msg.strip()

        # 좌표 정보
        if "ra" in msg_lower and "dec" in msg_lower:
            info["coordinates"] = msg.strip()

    return info
