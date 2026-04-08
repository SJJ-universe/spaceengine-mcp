"""Phase 7 Tools — pywin32 키보드 확장 (콘솔 외 기능)

비디오 녹화, 천체 검색, 고해상도 스크린샷, 모드 전환, 범용 키보드 단축키
"""

from typing import Literal

from spaceengine_mcp.bridges import keyboard_bridge


def register_tools(mcp):

    @mcp.tool()
    def record_video(
        action: Literal["configure", "start", "stop"] = "start",
    ) -> dict:
        """
        SpaceEngine 비디오 녹화를 제어합니다.

        Args:
            action: configure(F9으로 설정창 열기), start(Ctrl+F9 녹화 시작), stop(Ctrl+F9 녹화 중지)
        """
        if action == "configure":
            return keyboard_bridge.send_key("f9")
        elif action in ("start", "stop"):
            return keyboard_bridge.send_key("f9", modifiers=["ctrl"])
        return {"status": "error", "message": f"지원하지 않는 action: {action}"}

    @mcp.tool()
    def search_object(query: str) -> dict:
        """
        SpaceEngine F3 검색창을 열어 천체를 검색합니다.
        검색 후 천체가 선택되며, navigate_to로 이동할 수 있습니다.

        Args:
            query: 검색할 천체 이름 (예: "Mars", "Betelgeuse", "NGC 224")
        """
        return keyboard_bridge.send_key_then_type("f3", query, delay_after_key=1.0)

    @mcp.tool()
    def hi_res_screenshot() -> dict:
        """
        SpaceEngine 고해상도 스크린샷 대화상자를 엽니다.
        Shift+F2로 접근합니다. 대화상자에서 해상도를 설정하세요.
        """
        return keyboard_bridge.send_key("f2", modifiers=["shift"])

    @mcp.tool()
    def switch_mode(
        mode: Literal["free", "ship", "aircraft"] = "free",
    ) -> dict:
        """
        SpaceEngine 카메라/비행 모드를 전환합니다.

        Args:
            mode: free(자유 카메라=1), ship(우주선=2), aircraft(항공기=3)
        """
        mode_key_map = {
            "free": "1",
            "ship": "2",
            "aircraft": "3",
        }
        key = mode_key_map[mode]
        return keyboard_bridge.send_key(key)

    @mcp.tool()
    def keyboard_shortcut(
        key: str,
        modifiers: list[str] | None = None,
    ) -> dict:
        """
        SpaceEngine에 임의의 키보드 단축키를 전송합니다.
        ESC 키는 안전을 위해 차단됩니다.

        Args:
            key: 키 이름 (f1~f12, 0~9, a~z, space, enter, tab, up, down 등)
            modifiers: 수정자 키 목록 (ctrl, shift, alt)
        """
        return keyboard_bridge.send_key(key, modifiers)
