"""Phase 4 Tools — 사운드, 상태 관리, 고급 제어"""

from spaceengine_mcp.bridges.script_bridge import sanitize_object_name, normalize_overlay_name


def register_tools(mcp, script_bridge, catalog_bridge):

    @mcp.tool()
    async def play_sound(filename: str, volume: float | None = None) -> dict:
        """
        SpaceEngine에서 사운드 파일을 재생합니다.

        Args:
            filename: 사운드 파일 이름 (data/sounds/ 또는 addons/*/sounds/ 내)
            volume: 볼륨 (0.0 ~ 1.0)
        """
        commands = script_bridge.build_sound_commands("play", filename=filename, volume=volume)
        if not commands:
            return {"status": "error", "message": "사운드 파일 이름이 필요합니다."}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def stop_sound() -> dict:
        """현재 재생 중인 사운드를 중지합니다."""
        commands = script_bridge.build_sound_commands("stop")
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def save_state() -> dict:
        """현재 SpaceEngine 상태(카메라 위치, 시간 등)를 저장합니다."""
        commands = ["SaveVars"]
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def restore_state() -> dict:
        """save_state로 저장한 SpaceEngine 상태를 복원합니다."""
        commands = ["RestoreVars"]
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def create_flyby(
        target: str,
        start_dist: float = 10.0,
        end_dist: float = 2.0,
        flyby_duration: float = 15.0,
        transition_time: float = 5.0,
    ) -> dict:
        """
        천체 근접 비행(플라이바이) 시나리오를 실행합니다.

        Args:
            target: 천체 이름
            start_dist: 시작 거리 (천체 반경 배수)
            end_dist: 종료 거리 (천체 반경 배수)
            flyby_duration: 비행 시간 (초)
            transition_time: 초기 이동 시간 (초)
        """
        context = {
            "target": sanitize_object_name(target),
            "start_dist": start_dist,
            "end_dist": end_dist,
            "flyby_duration": flyby_duration,
            "transition_time": transition_time,
        }
        try:
            script_path = script_bridge.generate_from_template("flyby.se.j2", context)
        except Exception:
            safe_target = sanitize_object_name(target)
            commands = [
                'UserMoveControl "Free"',
                'UserRotationControl "Free"',
                'UserTimeControl "Free"',
                f'Select "{safe_target}"',
                f'Goto {{ Time {transition_time} DistRad {start_dist} }}',
                f'Wait {transition_time}',
                f'Goto {{ Time {flyby_duration} DistRad {end_dist} }}',
                f'Wait {flyby_duration}',
            ]
            script_path = script_bridge.generate_script(commands, filename=f"mcp_flyby_{safe_target}.se")

        result = await script_bridge.execute_script(script_path)
        result["flyby_target"] = target
        return result

    @mcp.tool()
    async def create_comparison(
        objects: list[str],
        distance_rad: float = 5.0,
        wait_seconds: int = 5,
    ) -> dict:
        """
        여러 천체를 순서대로 방문하여 크기/특성을 비교합니다.

        Args:
            objects: 비교할 천체 이름 리스트 (예: ["Earth", "Mars", "Jupiter"])
            distance_rad: 관측 거리 (천체 반경 배수)
            wait_seconds: 각 천체에서 머무는 시간 (초)
        """
        commands = [
            'UserMoveControl "Free"',
            'UserRotationControl "Free"',
            'UserTimeControl "Free"',
        ]
        for obj_name in objects:
            safe_name = sanitize_object_name(obj_name)
            commands.append(f'Select "{safe_name}"')
            commands.append(f'Goto {{ Time 4 DistRad {distance_rad} }}')
            commands.append('Wait 4')
            commands.append(f'Print "{safe_name}" {{ Time {wait_seconds} }}')
            commands.append(f'Wait {wait_seconds}')
            commands.append('HidePrint')
        script_path = script_bridge.generate_script(commands, filename="mcp_comparison.se")
        result = await script_bridge.execute_script(script_path)
        result["compared_objects"] = objects
        return result

    @mcp.tool()
    async def set_rendering(setting: str, value: str) -> dict:
        """
        SpaceEngine 렌더링 설정을 변경합니다.

        Args:
            setting: 설정 이름 (Orbits, Labels, Atmospheres, Clouds 등)
            value: "show", "hide", 또는 "toggle"
        """
        setting = normalize_overlay_name(setting)
        if value == "show":
            commands = [f"Show {setting}"]
        elif value == "hide":
            commands = [f"Hide {setting}"]
        elif value == "toggle":
            commands = [f"Toggle {setting}"]
        else:
            return {"status": "error", "message": f"유효하지 않은 값: {value}. show/hide/toggle 사용."}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def wait_and_execute(wait_seconds: float, commands_after: list[str]) -> dict:
        """
        지정 시간 대기 후 명령어를 실행합니다.

        Args:
            wait_seconds: 대기 시간 (초)
            commands_after: 대기 후 실행할 SE 명령어 리스트
        """
        all_commands = [f"Wait {wait_seconds}"] + commands_after
        script_path = script_bridge.generate_script(all_commands)
        return await script_bridge.execute_script(script_path)
