"""Phase 3 Tools — 카메라, 스크린샷, 로그, 메시지"""

from typing import Literal

from spaceengine_mcp.bridges.log_bridge import parse_log_tail, search_log, get_log_errors, get_log_stats


def register_tools(mcp, script_bridge, config):

    @mcp.tool()
    async def control_camera(
        dist: float | None = None,
        dist_rad: float | None = None,
        fov: float | None = None,
        time: float = 3.0,
    ) -> dict:
        """
        SpaceEngine 카메라 파라미터를 조정합니다 (줌, 시야각 등).

        Args:
            dist: 관측 거리 (km 단위 절대값)
            dist_rad: 관측 거리 (천체 반경 배수)
            fov: 시야각 (Field of View, 도 단위)
            time: 전환 시간 (초)
        """
        commands = script_bridge.build_camera_commands(dist=dist, dist_rad=dist_rad, fov=fov, time=time)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def take_screenshot() -> dict:
        """
        SpaceEngine에서 현재 화면의 스크린샷을 캡처합니다.
        결과 파일은 SE의 screenshots/ 디렉토리에 저장됩니다.
        """
        commands = script_bridge.build_screenshot_command()
        script_path = script_bridge.generate_script(commands)
        result = await script_bridge.execute_script(script_path)
        result["screenshots_dir"] = str(config.screenshots_dir)
        return result

    @mcp.tool()
    async def show_message(text: str, duration: float = 5.0) -> dict:
        """
        SpaceEngine 화면에 텍스트 메시지를 표시합니다.

        Args:
            text: 표시할 메시지 텍스트
            duration: 표시 시간 (초)
        """
        commands = script_bridge.build_message_commands(text=text, duration=duration)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def hide_message() -> dict:
        """화면에 표시 중인 메시지를 숨깁니다."""
        commands = script_bridge.build_message_commands(text="", show=False)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def toggle_gui(visible: bool) -> dict:
        """
        SpaceEngine UI(메뉴, 정보 패널 등)를 표시하거나 숨깁니다.

        Args:
            visible: True=UI 표시, False=UI 숨김
        """
        commands = script_bridge.build_gui_commands(visible=visible)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def follow_object(
        target: str,
        mode: Literal["follow", "track", "unfollow", "untrack"] = "follow",
    ) -> dict:
        """
        천체를 추적하거나 추적을 해제합니다.

        Args:
            target: 천체 이름
            mode: follow(카메라 따라감), track(시선 고정), unfollow/untrack(해제)
        """
        commands = script_bridge.build_follow_commands(target=target, mode=mode)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    def read_log(
        lines: int = 50,
        search_pattern: str | None = None,
        errors_only: bool = False,
    ) -> dict:
        """
        SpaceEngine 로그 파일(se.log)을 읽어 분석합니다.

        Args:
            lines: 읽을 줄 수 (기본 50, 최대 200)
            search_pattern: 검색할 정규식 패턴 (None이면 마지막 N줄)
            errors_only: True이면 오류/경고만 필터링
        """
        log_path = config.log_file
        stats = get_log_stats(log_path)

        if errors_only:
            entries = get_log_errors(log_path)
        elif search_pattern:
            entries = search_log(log_path, search_pattern)
        else:
            entries = parse_log_tail(log_path, min(lines, 200))

        return {"stats": stats, "entries": entries}
