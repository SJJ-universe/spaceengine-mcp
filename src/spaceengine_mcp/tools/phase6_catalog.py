"""Phase 6 Tools — 카탈로그 확장 (.sc 고급)

위성, 무게중심, 고리, 대기, 지형, 성운, 은하 생성 + 확장 검색
"""

from spaceengine_mcp.models import (
    MoonParams, BarycenterParams, RingSystemParams,
    AtmosphereParams, SurfaceParams, NebulaParams, GalaxyParams,
)
from spaceengine_mcp.bridges.script_bridge import sanitize_object_name


def register_tools(mcp, script_bridge, catalog_bridge):
    from spaceengine_mcp.bridges.catalog_bridge import CelestialObject

    @mcp.tool()
    async def create_moon(params: MoonParams, navigate_after: bool = True) -> dict:
        """
        위성(Moon)을 생성합니다.

        Args:
            params: 위성 파라미터 (이름, 부모 행성, 질량, 반경, 궤도 등)
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

        moon_props: dict = {
            "Class": f'"{params.moon_class}"',
            "Mass": str(params.mass),
            "Radius": str(params.radius),
            "Orbit": orbit_props,
        }
        if params.tidal_locked:
            moon_props["TidalLocked"] = "true"

        obj = CelestialObject(
            obj_type="Moon", name=safe_name,
            parent_body=safe_parent, properties=moon_props,
        )
        catalog_path = catalog_bridge.write_planet_catalog([obj], catalog_name=safe_name)
        result: dict = {"status": "created", "catalog": str(catalog_path), "moon": safe_name}

        if navigate_after:
            commands = script_bridge.build_navigation_commands(target=safe_name, mode="goto", distance_rad=5.0)
            script_path = script_bridge.generate_script(commands)
            nav_result = await script_bridge.execute_script(script_path)
            result["navigation"] = nav_result

        return result

    @mcp.tool()
    def create_barycenter(params: BarycenterParams) -> dict:
        """
        쌍성계/쌍행성계의 무게중심(Barycenter)을 생성합니다.

        Args:
            params: 무게중심 파라미터 (이름, 질량)
        """
        safe_name = sanitize_object_name(params.name)
        obj = CelestialObject(
            obj_type="Barycenter",
            name=safe_name,
            properties={"Mass": str(params.mass)},
        )
        catalog_path = catalog_bridge.write_star_catalog([obj], catalog_name=safe_name)
        return {"status": "created", "catalog": str(catalog_path), "barycenter": safe_name}

    @mcp.tool()
    def create_ring_system(
        target_planet: str,
        rings: RingSystemParams,
    ) -> dict:
        """
        행성에 고리 시스템을 추가합니다.
        새로운 카탈로그 엔트리로 생성되어 SE 재시작 시 적용됩니다.

        Args:
            target_planet: 고리를 추가할 행성 이름
            rings: 고리 파라미터 (내부/외부 반경, 구성)
        """
        safe_planet = sanitize_object_name(target_planet)

        ring_props: dict = {
            "InnerRadius": str(rings.inner_radius),
            "OuterRadius": str(rings.outer_radius),
        }
        if rings.texture:
            ring_props["Texture"] = f'"{sanitize_object_name(rings.texture)}"'
        if rings.composition:
            ring_props["Composition"] = f'"{rings.composition}"'

        # 행성 override 엔트리: Rings 블록만 포함
        obj = CelestialObject(
            obj_type="Planet",
            name=safe_planet,
            properties={"Rings": ring_props},
        )
        catalog_path = catalog_bridge.write_planet_catalog(
            [obj], catalog_name=f"{safe_planet}_Rings"
        )
        return {"status": "created", "catalog": str(catalog_path), "planet": safe_planet}

    @mcp.tool()
    def edit_atmosphere(
        target_body: str,
        atmosphere: AtmosphereParams,
    ) -> dict:
        """
        천체의 대기 설정을 추가/수정합니다.

        Args:
            target_body: 대상 천체 이름
            atmosphere: 대기 파라미터 (기압, 높이, 조성, 온실효과)
        """
        safe_body = sanitize_object_name(target_body)

        atmo_props: dict = {
            "Pressure": str(atmosphere.pressure),
        }
        if atmosphere.height is not None:
            atmo_props["Height"] = str(atmosphere.height)
        if atmosphere.greenhouse is not None:
            atmo_props["Greenhouse"] = str(atmosphere.greenhouse)
        if atmosphere.composition:
            comp_props = {}
            for gas, fraction in atmosphere.composition.items():
                comp_props[gas] = str(fraction)
            atmo_props["Composition"] = comp_props

        obj = CelestialObject(
            obj_type="Planet",
            name=safe_body,
            properties={"Atmosphere": atmo_props},
        )
        catalog_path = catalog_bridge.write_planet_catalog(
            [obj], catalog_name=f"{safe_body}_Atmosphere"
        )
        return {"status": "created", "catalog": str(catalog_path), "body": safe_body}

    @mcp.tool()
    def edit_surface(
        target_body: str,
        surface: SurfaceParams,
    ) -> dict:
        """
        천체의 지형/표면 설정을 추가/수정합니다.

        Args:
            target_body: 대상 천체 이름
            surface: 지형 파라미터 (스타일, 컬러맵, 높이 스케일, 적설 고도)
        """
        safe_body = sanitize_object_name(target_body)

        surf_props: dict = {}
        if surface.style is not None:
            surf_props["Style"] = str(surface.style)
        if surface.color_map:
            surf_props["ColorMap"] = f'"{sanitize_object_name(surface.color_map)}"'
        if surface.height_scale is not None:
            surf_props["HeightScale"] = str(surface.height_scale)
        if surface.snow_level is not None:
            surf_props["SnowLevel"] = str(surface.snow_level)

        if not surf_props:
            return {"status": "error", "message": "최소 하나의 지형 파라미터가 필요합니다."}

        obj = CelestialObject(
            obj_type="Planet",
            name=safe_body,
            properties={"Surface": surf_props},
        )
        catalog_path = catalog_bridge.write_planet_catalog(
            [obj], catalog_name=f"{safe_body}_Surface"
        )
        return {"status": "created", "catalog": str(catalog_path), "body": safe_body}

    @mcp.tool()
    async def create_nebula(params: NebulaParams, navigate_after: bool = True) -> dict:
        """
        성운(Nebula)을 생성합니다.

        Args:
            params: 성운 파라미터 (이름, 유형, 반경, 밝기)
            navigate_after: 생성 후 카메라 이동 여부
        """
        safe_name = sanitize_object_name(params.name)

        nebula_props: dict = {
            "Type": f'"{params.nebula_type}"',
            "Radius": str(params.radius),
            "Brightness": str(params.brightness),
        }
        if params.ra is not None:
            nebula_props["RA"] = str(params.ra)
        if params.dec is not None:
            nebula_props["Dec"] = str(params.dec)

        obj = CelestialObject(obj_type="Nebula", name=safe_name, properties=nebula_props)
        catalog_path = catalog_bridge.write_nebula_catalog([obj], catalog_name=safe_name)
        result: dict = {"status": "created", "catalog": str(catalog_path), "nebula": safe_name}

        if navigate_after:
            commands = script_bridge.build_navigation_commands(target=safe_name, mode="goto", distance_rad=5.0)
            script_path = script_bridge.generate_script(commands)
            nav_result = await script_bridge.execute_script(script_path)
            result["navigation"] = nav_result

        return result

    @mcp.tool()
    async def create_galaxy(params: GalaxyParams, navigate_after: bool = True) -> dict:
        """
        은하(Galaxy)를 생성합니다.

        Args:
            params: 은하 파라미터 (이름, 유형, 반경, 질량)
            navigate_after: 생성 후 카메라 이동 여부
        """
        safe_name = sanitize_object_name(params.name)

        galaxy_props: dict = {
            "Type": f'"{params.galaxy_type}"',
            "Radius": str(params.radius),
            "Mass": str(params.mass),
        }
        if params.ra is not None:
            galaxy_props["RA"] = str(params.ra)
        if params.dec is not None:
            galaxy_props["Dec"] = str(params.dec)

        obj = CelestialObject(obj_type="Galaxy", name=safe_name, properties=galaxy_props)
        catalog_path = catalog_bridge.write_galaxy_catalog([obj], catalog_name=safe_name)
        result: dict = {"status": "created", "catalog": str(catalog_path), "galaxy": safe_name}

        if navigate_after:
            commands = script_bridge.build_navigation_commands(target=safe_name, mode="goto", distance_rad=50.0)
            script_path = script_bridge.generate_script(commands)
            nav_result = await script_bridge.execute_script(script_path)
            result["navigation"] = nav_result

        return result

    @mcp.tool()
    def search_catalog_v2(
        query: str,
        obj_type: str | None = None,
    ) -> list[dict]:
        """
        모든 카탈로그 디렉토리에서 천체를 검색합니다 (V2 재귀 파서 사용).
        stars, planets, nebulae, galaxies 전체를 대상으로 합니다.

        Args:
            query: 검색어 (천체 이름 부분 일치)
            obj_type: 천체 유형 필터 (Star, Planet, Moon, Nebula, Galaxy 등)
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
