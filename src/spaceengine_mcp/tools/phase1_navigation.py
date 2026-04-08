"""Phase 1 Tools — 탐색 / 내비게이션"""

from typing import Literal


def register_tools(mcp, script_bridge, catalog_bridge):

    @mcp.tool()
    async def navigate_to(
        target: str,
        mode: Literal["goto", "center", "follow"] = "goto",
        distance_rad: float = 3.0,
        transition_time: float = 5.0,
    ) -> dict:
        """
        SpaceEngine에서 특정 천체로 카메라를 이동합니다.

        Args:
            target: 천체 이름 (예: "Mars", "Sol", "Andromeda")
            mode: 이동 방식 — goto(이동), center(회전만), follow(추적)
            distance_rad: 관측 거리 (천체 반경의 배수)
            transition_time: 이동 전환 시간 (초)
        """
        commands = script_bridge.build_navigation_commands(
            target=target, mode=mode, distance_rad=distance_rad, transition_time=transition_time
        )
        script_path = script_bridge.generate_script(commands)
        result = await script_bridge.execute_script(script_path)
        result["commands"] = commands
        return result

    @mcp.tool()
    async def run_script(commands: list[str]) -> dict:
        """
        SpaceEngine .se 명령어 리스트를 직접 실행합니다.

        허용 명령어: Select, Goto, Center, Follow, Free, Track, Untrack, Date,
                     TimeScale, StopTime, StartTime, Show, Hide, Print, HidePrint,
                     FOV, Orbit, StopOrbit, PlaySplinePath, SaveVars, RestoreVars,
                     Wait, WaitTrigger, Screenshot, Set, Interpolate, FadeOut, FadeIn

        Args:
            commands: SE 명령어 문자열 리스트 (예: ['Select "Mars"', 'Goto { Time 5 DistRad 3 }', 'Wait 5'])
        """
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    def search_catalog(query: str, obj_type: str | None = None) -> list[dict]:
        """
        MCP가 생성한 커스텀 카탈로그에서 천체를 검색합니다.
        (기본 SE 카탈로그는 .pak 압축 파일이므로 검색 불가)

        Args:
            query: 검색어 (천체 이름 부분 일치)
            obj_type: 천체 유형 필터 (Star, Planet, Moon 등) — None이면 전체
        """
        results = catalog_bridge.search_catalogs(query, obj_type)
        return [
            {
                "type": obj.obj_type,
                "name": obj.name,
                "parent": obj.parent_body,
                "properties": obj.properties,
            }
            for obj in results
        ]
