"""Phase 2 Tools — 천체 생성, 시간, 오버레이"""

from typing import Literal

from spaceengine_mcp.models import StarParams, PlanetParams, TourStop
from spaceengine_mcp.bridges.script_bridge import sanitize_object_name


def register_tools(mcp, script_bridge, catalog_bridge):
    # CelestialObject 임포트는 함수 내에서 수행 (순환 참조 방지)
    from spaceengine_mcp.bridges.catalog_bridge import CelestialObject

    @mcp.tool()
    async def create_star(params: StarParams, navigate_after: bool = True) -> dict:
        """
        커스텀 항성을 SpaceEngine 애드온 카탈로그에 생성합니다.

        Args:
            params: 항성 파라미터 (이름, 분광형, 질량, 반경, 온도, 광도)
            navigate_after: 생성 후 해당 항성으로 카메라 이동 여부
        """
        safe_name = sanitize_object_name(params.name)
        obj = CelestialObject(
            obj_type="Star",
            name=safe_name,
            properties={
                "Class": f'"{params.spectral_class}"',
                "Mass": str(params.mass),
                "Radius": str(params.radius),
                "Temperature": str(params.temperature),
                "Luminosity": str(params.luminosity),
            },
        )
        catalog_path = catalog_bridge.write_star_catalog([obj], catalog_name=safe_name)
        result: dict = {"status": "created", "catalog": str(catalog_path), "star": safe_name}

        if navigate_after:
            # navigate_to는 이미 등록된 phase1 tool이므로 bridge 직접 호출
            commands = script_bridge.build_navigation_commands(target=safe_name, mode="goto", distance_rad=50.0)
            script_path = script_bridge.generate_script(commands)
            nav_result = await script_bridge.execute_script(script_path)
            result["navigation"] = nav_result

        return result

    @mcp.tool()
    async def create_planet(params: PlanetParams, navigate_after: bool = True) -> dict:
        """
        커스텀 행성을 SpaceEngine 애드온 카탈로그에 생성합니다.

        Args:
            params: 행성 파라미터
            navigate_after: 생성 후 카메라 이동 여부
        """
        safe_name = sanitize_object_name(params.name)
        safe_parent = sanitize_object_name(params.parent)

        orbit_props = {
            "SemiMajorAxis": str(params.orbit.semi_major_axis),
            "Eccentricity": str(params.orbit.eccentricity),
            "Inclination": str(params.orbit.inclination),
        }
        if params.orbit.period is not None:
            orbit_props["Period"] = str(params.orbit.period)

        planet_props: dict = {
            "Class": f'"{params.planet_class}"',
            "Mass": str(params.mass),
            "Radius": str(params.radius),
            "Orbit": orbit_props,
        }
        if params.has_atmosphere:
            planet_props["Atmosphere"] = {"Pressure": "1.0"}
        if params.has_water:
            planet_props["Ocean"] = {"Height": "0.1"}

        obj = CelestialObject(obj_type="Planet", name=safe_name, parent_body=safe_parent, properties=planet_props)
        catalog_path = catalog_bridge.write_planet_catalog([obj], catalog_name=safe_name)
        result: dict = {"status": "created", "catalog": str(catalog_path), "planet": safe_name}

        if navigate_after:
            commands = script_bridge.build_navigation_commands(target=safe_name, mode="goto", distance_rad=5.0)
            script_path = script_bridge.generate_script(commands)
            nav_result = await script_bridge.execute_script(script_path)
            result["navigation"] = nav_result

        return result

    @mcp.tool()
    async def create_tour(title: str, stops: list[TourStop], loop: bool = False, transition_time: float = 5.0) -> dict:
        """
        교육용 우주 투어 스크립트를 생성하고 SpaceEngine에서 실행합니다.

        Args:
            title: 투어 제목
            stops: 방문할 천체 목록 (이름, 대기 시간, 거리, 메시지)
            loop: 반복 재생 여부
            transition_time: 천체 간 이동 시간 (초)
        """
        context = {
            "title": title,
            "stops": [s.model_dump() if hasattr(s, 'model_dump') else s for s in stops],
            "loop": loop,
            "transition_time": transition_time,
        }
        try:
            script_path = script_bridge.generate_from_template("tour.se.j2", context)
        except Exception:
            commands = [
                'UserMoveControl "Free"',
                'UserRotationControl "Free"',
                'UserTimeControl "Free"',
            ]
            for stop in stops:
                safe_target = sanitize_object_name(stop.target)
                commands.append(f'Select "{safe_target}"')
                commands.append(f'Goto {{ Time {transition_time} DistRad {stop.distance_rad} }}')
                commands.append(f'Wait {transition_time}')
                if stop.message:
                    safe_msg = stop.message.replace('"', "'")
                    commands.append(f'Print "{safe_msg}" {{ Time {stop.wait_seconds} }}')
                commands.append(f'Wait {stop.wait_seconds}')
                commands.append('HidePrint')
            script_path = script_bridge.generate_script(commands, filename=f"mcp_tour_{title[:20].replace(' ', '_')}.se")

        result = await script_bridge.execute_script(script_path)
        result["tour_title"] = title
        result["stops_count"] = len(stops)
        return result

    @mcp.tool()
    async def set_time(date: str | None = None, rate: float | None = None) -> dict:
        """
        SpaceEngine 시뮬레이션 시간을 설정합니다.

        Args:
            date: 날짜/시간 (ISO 8601, 예: "2024-04-08T18:00:00")
            rate: 시간 흐름 속도 (양수=배속, 0=StopTime, 음수=역방향)
        """
        commands = script_bridge.build_time_commands(date_iso=date, rate=rate)
        if not commands:
            return {"status": "error", "message": "date 또는 rate 중 하나는 제공해야 합니다."}
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    async def toggle_overlay(overlay: str, visible: bool) -> dict:
        """
        SpaceEngine 오버레이 표시/숨김을 토글합니다.

        Args:
            overlay: 오버레이 이름 (Orbits, Labels, Constellations, Atmospheres 등)
            visible: True=Show, False=Hide
        """
        commands = script_bridge.build_overlay_commands(overlay=overlay, visible=visible)
        script_path = script_bridge.generate_script(commands)
        return await script_bridge.execute_script(script_path)

    @mcp.tool()
    def list_addons(category: str = "all") -> list[dict]:
        """
        설치된 MCP 애드온 카탈로그 목록을 반환합니다.

        Args:
            category: "stars", "planets", "all" 중 선택
        """
        return catalog_bridge.list_addon_catalogs(category=category)

    @mcp.tool()
    def delete_addon(catalog_name: str) -> dict:
        """
        MCP가 생성한 커스텀 카탈로그를 삭제합니다. (MCP_ 접두사 카탈로그만 삭제 가능)

        Args:
            catalog_name: 카탈로그 이름
        """
        deleted = catalog_bridge.delete_catalog(catalog_name)
        return {"deleted": deleted, "catalog_name": catalog_name}
