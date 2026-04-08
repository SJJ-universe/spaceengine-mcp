"""Phase 8 Tools — 파일시스템 브릿지

설정 파일 편집, 애드온 관리, 우주선 정의, 천체 데이터 내보내기
"""

from typing import Literal


def register_tools(mcp, config_bridge, catalog_bridge, script_bridge, config):

    @mcp.tool()
    def edit_config(
        key: str | None = None,
        value: str | None = None,
        list_all: bool = False,
    ) -> dict:
        """
        SpaceEngine 사용자 설정 파일(main-user.cfg)을 읽거나 수정합니다.
        수정 시 자동으로 .bak 백업이 생성됩니다.

        Args:
            key: 설정 키 이름 (None이면 list_all 사용)
            value: 설정할 값 (None이면 현재 값 읽기)
            list_all: True이면 모든 설정 항목 반환
        """
        if list_all:
            entries = config_bridge.list_config()
            return {"status": "ok", "entries": entries, "count": len(entries)}
        if key is None:
            return {"status": "error", "message": "key 또는 list_all=True가 필요합니다."}
        if value is None:
            # 읽기 모드
            current = config_bridge.get_value(key)
            if current is None:
                return {"status": "ok", "key": key, "value": None, "found": False}
            return {"status": "ok", "key": key, "value": current, "found": True}
        # 쓰기 모드
        return config_bridge.set_value(key, value)

    @mcp.tool()
    def manage_addons(
        action: Literal["list", "remove"] = "list",
        category: str = "all",
        addon_name: str | None = None,
    ) -> dict:
        """
        MCP 애드온 카탈로그를 관리합니다.

        Args:
            action: list(목록 조회), remove(삭제 — MCP_ 접두사만)
            category: 카테고리 필터 (all, stars, planets, nebulae, galaxies)
            addon_name: 삭제할 카탈로그 이름 (action=remove일 때 필수)
        """
        if action == "list":
            catalogs = catalog_bridge.list_addon_catalogs(category)
            return {"status": "ok", "catalogs": catalogs, "count": len(catalogs)}
        elif action == "remove":
            if not addon_name:
                return {"status": "error", "message": "삭제할 addon_name이 필요합니다."}
            deleted = catalog_bridge.delete_catalog(addon_name)
            return {"status": "ok", "deleted": deleted, "addon_name": addon_name}
        return {"status": "error", "message": f"지원하지 않는 action: {action}"}

    @mcp.tool()
    def create_spacecraft(
        name: str,
        mass: float = 1000.0,
        max_thrust: float = 10000.0,
        fuel_capacity: float = 1000.0,
    ) -> dict:
        """
        SpaceEngine 우주선 정의 파일(.sss)을 생성합니다.
        addons/models/spacecraft/ 디렉토리에 저장됩니다.

        Args:
            name: 우주선 이름
            mass: 질량 (kg)
            max_thrust: 최대 추력 (N)
            fuel_capacity: 연료 용량 (kg)
        """
        from spaceengine_mcp.bridges.script_bridge import sanitize_object_name
        safe_name = sanitize_object_name(name)

        # .sss 파일 생성
        spacecraft_dir = config.install_path / "addons" / "models" / "spacecraft"
        spacecraft_dir.mkdir(parents=True, exist_ok=True)
        sss_path = spacecraft_dir / f"MCP_{safe_name}.sss"

        sss_content = f"""// SpaceEngine Spacecraft Definition — MCP Generated
// Name: {safe_name}

Spacecraft "{safe_name}"
{{
    Mass            {mass}
    MaxThrust       {max_thrust}
    FuelCapacity    {fuel_capacity}
}}
"""
        sss_path.write_text(sss_content, encoding="utf-8")
        return {
            "status": "created",
            "path": str(sss_path),
            "spacecraft": safe_name,
        }

    @mcp.tool()
    def export_object_data(
        query: str,
        obj_type: str | None = None,
    ) -> dict:
        """
        카탈로그에서 천체 데이터를 검색하고 구조화된 형태로 내보냅니다.

        Args:
            query: 검색어 (천체 이름 부분 일치)
            obj_type: 천체 유형 필터 (Star, Planet, Moon, Nebula, Galaxy 등)
        """
        results = catalog_bridge.search_catalogs(query, obj_type)
        objects = []
        for obj in results:
            objects.append({
                "type": obj.obj_type,
                "name": obj.name,
                "parent": obj.parent_body,
                "properties": obj.properties,
            })
        return {
            "status": "ok",
            "query": query,
            "count": len(objects),
            "objects": objects,
        }
