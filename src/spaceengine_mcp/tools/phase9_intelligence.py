"""Phase 9 Tools — 인텔리전스 레이어

SE 상태 모니터링, 명령 검증, 화면 OCR, 스마트 내비게이션
"""

from typing import Literal


def register_tools(mcp, state_bridge, script_bridge):

    @mcp.tool()
    def read_se_state() -> dict:
        """
        SpaceEngine의 현재 상태를 반환합니다.
        선택된 천체, 카메라 정보, 최근 오류 등을 포함합니다.
        """
        return state_bridge.get_current_state()

    @mcp.tool()
    def verify_command(
        expected_pattern: str,
        timeout: float = 10.0,
    ) -> dict:
        """
        명령어 실행 후 se.log를 모니터링하여 결과를 검증합니다.
        예: navigate_to("Mars") 실행 후 verify_command("Selected.*Mars")

        Args:
            expected_pattern: 기대하는 로그 패턴 (정규식)
            timeout: 최대 대기 시간 (초)
        """
        entry = state_bridge.wait_for_log_entry(expected_pattern, timeout=timeout)
        if entry is not None:
            return {"status": "ok", "verified": True, "log_entry": entry}
        return {"status": "ok", "verified": False, "message": f"패턴 '{expected_pattern}'을 {timeout}초 내에 찾지 못함"}

    @mcp.tool()
    def screen_capture_ocr(
        region: str | None = None,
    ) -> dict:
        """
        SpaceEngine 화면을 캡처하고 OCR로 텍스트를 추출합니다.
        pytesseract + Pillow가 필요합니다.

        Args:
            region: 캡처 영역 ("full" 또는 "x1,y1,x2,y2" 형식). None이면 전체 화면.
        """
        region_tuple = None
        if region and region != "full":
            try:
                parts = [int(x.strip()) for x in region.split(",")]
                if len(parts) == 4:
                    region_tuple = tuple(parts)
            except ValueError:
                return {"status": "error", "message": f"잘못된 영역 형식: {region}. 'x1,y1,x2,y2' 사용."}

        return state_bridge.ocr_screen(region=region_tuple)

    @mcp.tool()
    async def smart_navigation(
        target: str,
        purpose: Literal["observe", "study", "cinematic", "close_up"] = "observe",
    ) -> dict:
        """
        목적에 맞는 파라미터를 자동 선택하여 천체로 이동합니다.

        Args:
            target: 천체 이름
            purpose: observe(일반 관측), study(학습/라벨 표시), cinematic(영상용/UI숨김), close_up(근접 촬영)
        """
        # 목적별 파라미터 프리셋
        presets = {
            "observe": {"distance_rad": 5.0, "transition_time": 5.0, "fov": None, "hide_gui": False, "show_labels": False},
            "study": {"distance_rad": 3.0, "transition_time": 4.0, "fov": None, "hide_gui": False, "show_labels": True},
            "cinematic": {"distance_rad": 4.0, "transition_time": 8.0, "fov": 30.0, "hide_gui": True, "show_labels": False},
            "close_up": {"distance_rad": 1.8, "transition_time": 6.0, "fov": 15.0, "hide_gui": False, "show_labels": False},
        }
        p = presets[purpose]

        all_commands = []

        # 1) 내비게이션
        nav_cmds = script_bridge.build_navigation_commands(
            target=target, mode="goto", distance_rad=p["distance_rad"], transition_time=p["transition_time"]
        )
        all_commands.extend(nav_cmds)

        # 2) FOV (선택적)
        if p["fov"]:
            all_commands.append(f"FOV {p['fov']}")

        # 3) GUI 숨기기 (cinematic) — SE에 ShowGUI 변수 없음
        if p["hide_gui"]:
            all_commands.append("HideAllDialogs")
            all_commands.append("HideAllToolbars")

        # 4) 라벨 표시 (study)
        if p["show_labels"]:
            all_commands.append("Show Labels")
            all_commands.append("Show Orbits")

        script_path = script_bridge.generate_script(all_commands)
        result = await script_bridge.execute_script(script_path)
        result["purpose"] = purpose
        result["preset"] = p
        return result
