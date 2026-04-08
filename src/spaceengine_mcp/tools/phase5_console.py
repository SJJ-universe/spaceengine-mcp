"""Phase 5 Tools — 콘솔 명령어 완전 도구화

변수 제어, 스플라인 경로, 웨이포인트, 카메라 비행, 속도, 페이드, 다이얼로그, 메시지
"""

from typing import Literal

from spaceengine_mcp.models import SplineKnot


def register_tools(mcp, script_bridge):

    @mcp.tool()
    async def set_variable(
        variable: str,
        action: Literal["set", "set_force", "set_u", "reset"] = "set",
        value: str | None = None,
    ) -> dict:
        """
        SpaceEngine 내부 변수를 설정/강제설정/초기화합니다.

        Args:
            variable: SE 변수 이름 (예: "StarBrightness", "AmbientLight")
            action: set(범위 검사 포함), set_force(강제), set_u(범위 무시), reset(기본값 복원)
            value: 설정할 값 (reset일 때는 불필요)
        """
        try:
            commands = script_bridge.build_variable_commands(variable, action, value)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def interpolate_variable(
        variable: str,
        target_value: float,
        duration: float = 5.0,
        function: Literal["linear", "quadric", "cubic", "sin", "exp", "revexp"] = "linear",
    ) -> dict:
        """
        SE 변수를 부드럽게 목표값까지 애니메이션합니다.

        Args:
            variable: SE 변수 이름
            target_value: 목표 값
            duration: 애니메이션 시간 (초)
            function: 보간 함수 (linear, quadric, cubic, sin, exp, revexp)
        """
        commands = script_bridge.build_interpolate_commands(variable, target_value, duration, function)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def create_spline_path(
        name: str,
        knots: list[SplineKnot],
        auto_play: bool = True,
        play_time: float = 30.0,
    ) -> dict:
        """
        스플라인 카메라 경로를 정의하고 선택적으로 재생합니다.
        시네마틱 카메라 워크에 사용됩니다.

        Args:
            name: 경로 이름
            knots: 키프레임 목록 (각 노트에서 천체 선택, Goto 파라미터, FOV, 대기 시간 지정)
            auto_play: True이면 정의 후 자동 재생
            play_time: 전체 재생 시간 (초)
        """
        knots_dicts = [k.model_dump() if hasattr(k, 'model_dump') else k for k in knots]
        commands = script_bridge.build_spline_path_commands(name, knots_dicts, auto_play, play_time)
        script_path = script_bridge.generate_script(commands)
        # 스플라인은 멀티라인 블록이므로 Run 모드로 실행
        return await script_bridge.execute_script(script_path, use_run=True)

    @mcp.tool()
    async def manage_waypoints(
        name: str = "",
        mode: Literal["create", "delete", "goto", "clear_all"] = "create",
    ) -> dict:
        """
        웨이포인트를 생성/삭제/이동합니다. 카메라 위치를 북마크하는 용도입니다.

        Args:
            name: 웨이포인트 이름 (clear_all일 때는 불필요)
            mode: create(현재 위치에 생성), delete(삭제), goto(이동), clear_all(전체 삭제)
        """
        try:
            commands = script_bridge.build_waypoint_commands(name, mode)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def camera_flight(
        action: Literal["fly", "turn", "orbit", "stop_fly", "stop_turn", "stop_orbit"] = "fly",
        x: float = 0,
        y: float = 0,
        z: float = 0,
    ) -> dict:
        """
        카메라 자유 비행/회전/궤도 운동을 제어합니다.

        Args:
            action: fly(이동), turn(회전), orbit(궤도), stop_fly/stop_turn/stop_orbit(중지)
            x: X축 성분 (좌우)
            y: Y축 성분 (상하)
            z: Z축 성분 (전후)
        """
        try:
            commands = script_bridge.build_flight_commands(action, x, y, z)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def set_speed(
        speed: float,
        unit: Literal["internal", "km"] = "internal",
    ) -> dict:
        """
        카메라 이동 속도를 설정합니다.

        Args:
            speed: 속도 값
            unit: "internal"(SE 내부 단위) 또는 "km"(km/s)
        """
        commands = script_bridge.build_speed_commands(speed, unit)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def fade_effect(
        action: Literal["fade_out", "fade_in"] = "fade_out",
        duration: float = 1.0,
    ) -> dict:
        """
        화면 페이드 아웃/인 효과를 적용합니다. 장면 전환에 사용됩니다.

        Args:
            action: fade_out(어두워짐) 또는 fade_in(밝아짐)
            duration: 효과 지속 시간 (초)
        """
        try:
            commands = script_bridge.build_fade_commands(action, duration)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def manage_dialogs(
        dialog_name: str = "",
        action: Literal["show", "hide", "hide_all"] = "show",
    ) -> dict:
        """
        SpaceEngine 다이얼로그를 열거나 닫습니다.

        Args:
            dialog_name: 다이얼로그 이름 (예: "ObjectInfo", "Settings")
            action: show(열기), hide(닫기), hide_all(전체 닫기)
        """
        try:
            commands = script_bridge.build_dialog_commands(dialog_name, action)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def advanced_message(
        text: str,
        wait_for_input: bool = False,
        duration: float = 5.0,
    ) -> dict:
        """
        BBCode 서식을 지원하는 메시지를 표시합니다.
        wait_for_input=True이면 사용자가 [Next] 버튼을 누를 때까지 대기합니다.

        Args:
            text: 메시지 텍스트 (BBCode 태그 사용 가능: [b], [i], [color=...] 등)
            wait_for_input: True이면 WaitMessage 모드 (사용자 입력 대기)
            duration: 표시 시간 (초, wait_for_input=False일 때만 적용)
        """
        commands = script_bridge.build_advanced_message_commands(text, wait_for_input, duration)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)
