"""Phase 10 Tools — 비행 시뮬레이터 (VR 제외)

우주선 조종, 오토파일럿, 도킹 보조, HUD 읽기
"""

from typing import Literal

from spaceengine_mcp.bridges import flight_bridge


def register_tools(mcp, script_bridge, state_bridge):

    @mcp.tool()
    def pilot_spacecraft(
        thrust_direction: Literal["forward", "backward", "left", "right", "up", "down"] | None = None,
        rotation: Literal["yaw_left", "yaw_right", "pitch_up", "pitch_down", "roll_left", "roll_right"] | None = None,
        duration: float = 1.0,
    ) -> dict:
        """
        우주선을 조종합니다. 추력 방향과 회전을 개별 또는 동시에 제어합니다.
        SE가 비행 모드(모드 2 또는 3)에서 실행 중이어야 합니다.

        Args:
            thrust_direction: 추력 방향 (forward/backward/left/right/up/down)
            rotation: 회전 축 (yaw_left/yaw_right/pitch_up/pitch_down/roll_left/roll_right)
            duration: 입력 지속 시간 (초)
        """
        results = {}
        if thrust_direction:
            results["thrust"] = flight_bridge.apply_thrust(thrust_direction, duration)
        if rotation:
            results["rotation"] = flight_bridge.apply_rotation(rotation, duration)
        if not results:
            return {"status": "error", "message": "thrust_direction 또는 rotation 중 하나는 지정해야 합니다."}
        return {"status": "ok", **results}

    @mcp.tool()
    async def autopilot_control(
        action: Literal["engage", "disengage", "set_target"] = "engage",
        target: str | None = None,
    ) -> dict:
        """
        오토파일럿을 제어합니다.

        Args:
            action: engage(활성화), disengage(비활성화), set_target(목표 설정 후 활성화)
            target: 목표 천체 (set_target일 때 필수)
        """
        if action == "set_target":
            if not target:
                return {"status": "error", "message": "target이 필��합니다."}
            # 천체 선택 → Goto 명령으로 오토파일럿 시뮬레이션
            commands = script_bridge.build_navigation_commands(
                target=target, mode="goto", distance_rad=3.0, transition_time=10.0
            )
            script_path = script_bridge.generate_script(commands)
            result = await script_bridge.execute_script(script_path)
            result["action"] = "set_target"
            result["target"] = target
            return result
        elif action == "engage":
            # SE에서 오토파일럿은 Select + Goto로 구현
            return {"status": "ok", "action": "engage", "message": "대상을 선택한 후 navigate_to 또는 set_target을 사용하세��."}
        elif action == "disengage":
            # Free 카메라로 전환
            commands = ["Free"]
            script_path = script_bridge.generate_script(commands)
            result = await script_bridge.execute_script(script_path)
            result["action"] = "disengage"
            return result
        return {"status": "error", "message": f"지원하지 않는 action: {action}"}

    @mcp.tool()
    async def docking_assist(
        target_station: str,
        approach_speed: float = 10.0,
    ) -> dict:
        """
        도킹 보조 — 목표 스테이션/우주선에 근접 접근합니다.
        매우 낮은 접근 거리와 느린 속도로 내비게이션을 수행합니다.

        Args:
            target_station: 도킹 대상 이름
            approach_speed: 접근 속도 계수 (낮을수록 느림)
        """
        # 느린 속도로 근접 접근
        commands = script_bridge.build_navigation_commands(
            target=target_station, mode="goto",
            distance_rad=1.2,  # 매우 가까�� 거리
            transition_time=max(15.0, 30.0 / approach_speed),  # 속도에 따른 전환 시간
        )
        # 속도 제한 추가
        commands.append(f"SpeedKm {approach_speed}")
        script_path = script_bridge.generate_script(commands)
        result = await script_bridge.execute_script(script_path)
        result["target_station"] = target_station
        result["approach_speed"] = approach_speed
        return result

    @mcp.tool()
    def flight_hud_read() -> dict:
        """
        비행 HUD 정보를 읽습니다.
        se.log에서 속도, FOV, TimeScale 등의 정보를 추출합니다.
        (OCR 기반 읽기는 pytesseract 설치 시 사용 가능)
        """
        state = state_bridge.get_current_state()
        hud_info = {
            "selected_object": state.get("selected_object"),
            "camera_info": state.get("camera_info"),
            "log_based": True,
        }

        # OCR 시도 (Pillow+pytesseract 있을 때만)
        ocr_result = state_bridge.ocr_screen()
        if ocr_result.get("status") == "ok":
            hud_info["ocr_text"] = ocr_result["text"]
            hud_info["log_based"] = False

        return {"status": "ok", "hud": hud_info}
