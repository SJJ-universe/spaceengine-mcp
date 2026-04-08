import pytest
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.catalog_bridge import CatalogBridge, CelestialObject


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_config(tmp_path):
    return SpaceEngineConfig(install_path=tmp_path)


@pytest.fixture
def bridge(tmp_config):
    return CatalogBridge(tmp_config)


# ── CelestialObject.to_sc ─────────────────────────────────────────────────────

def test_star_to_sc():
    obj = CelestialObject(
        obj_type="Star",
        name="TestStar",
        properties={"Class": '"G2 V"', "Mass": "1.0"},
    )
    sc = obj.to_sc()
    assert 'Star "TestStar"' in sc
    assert "Class" in sc
    assert "Mass" in sc


def test_planet_to_sc_with_parent():
    obj = CelestialObject(
        obj_type="Planet",
        name="TestPlanet",
        parent_body="TestStar",
        properties={"Class": '"Terra"', "Mass": "1.0"},
    )
    sc = obj.to_sc()
    assert 'ParentBody\t"TestStar"' in sc


# ── parse_sc_file ─────────────────────────────────────────────────────────────

def test_parse_sample_sc(bridge):
    results = bridge.parse_sc_file(FIXTURES / "sample.sc")
    names = [obj.name for obj in results]
    assert "MCP_TestStar" in names
    assert "MCP_TestPlanet" in names


def test_parse_planet_has_parent(bridge):
    results = bridge.parse_sc_file(FIXTURES / "sample.sc")
    planet = next(o for o in results if o.name == "MCP_TestPlanet")
    assert planet.parent_body == "MCP_TestStar"


# ── write & search ────────────────────────────────────────────────────────────

def test_write_star_catalog(bridge, tmp_config):
    obj = CelestialObject("Star", "MCP_WriteTest", properties={"Mass": "1.5"})
    path = bridge.write_star_catalog([obj], catalog_name="WriteTest")
    assert path.exists()
    assert path.name == "MCP_WriteTest.sc"


def test_search_finds_written_catalog(bridge):
    obj = CelestialObject("Star", "MCP_SearchMe", properties={"Mass": "1.0"})
    bridge.write_star_catalog([obj], catalog_name="SearchMe")
    results = bridge.search_catalogs("SearchMe")
    assert any(r.name == "MCP_SearchMe" for r in results)


def test_search_with_type_filter(bridge):
    star = CelestialObject("Star", "MCP_FilterStar", properties={})
    planet = CelestialObject("Planet", "MCP_FilterPlanet", parent_body="MCP_FilterStar", properties={})
    bridge.write_star_catalog([star], catalog_name="Filter")
    bridge.write_planet_catalog([planet], catalog_name="Filter")

    stars = bridge.search_catalogs("Filter", obj_type="Star")
    assert all(o.obj_type == "Star" for o in stars)


# ── safe_catalog_name ─────────────────────────────────────────────────────────

def test_catalog_name_gets_prefix(bridge):
    path = bridge.write_star_catalog([], catalog_name="NoPrefixTest")
    assert "MCP_" in path.name


def test_catalog_name_keeps_prefix(bridge):
    path = bridge.write_star_catalog([], catalog_name="MCP_AlreadyPrefixed")
    assert path.name.count("MCP_") == 1


# ── delete_catalog ────────────────────────────────────────────────────────────

def test_delete_catalog(bridge):
    obj = CelestialObject("Star", "MCP_DeleteMe", properties={})
    bridge.write_star_catalog([obj], catalog_name="DeleteMe")
    deleted = bridge.delete_catalog("DeleteMe")
    assert deleted is True


# ══════════════════════════════════════════════════════════════════════════════
# Phase 6 — 카탈로그 확장 테스트
# ══════════════════════════════════════════════════════════════════════════════

# ── Parser V2 (재귀 하강) ────────────────────────────────────────────────────

def test_parse_v2_3level_nesting(bridge):
    """3단계+ 중첩 (.sc Surface > Terrain) 파싱 검증"""
    results = bridge.parse_sc_file_v2(FIXTURES / "nested_3level.sc")
    assert len(results) == 1
    planet = results[0]
    assert planet.name == "MCP_DeepNested"
    assert planet.parent_body == "MCP_TestStar"
    # Surface > Terrain 중첩 확인
    assert "Surface" in planet.properties
    surface = planet.properties["Surface"]
    assert isinstance(surface, dict)
    assert "Terrain" in surface
    terrain = surface["Terrain"]
    assert isinstance(terrain, dict)
    assert terrain["HeightScale"] == "10"


def test_parse_v2_atmosphere_composition(bridge):
    """대기 조성 중첩 블록 파싱 검증"""
    results = bridge.parse_sc_file_v2(FIXTURES / "nested_3level.sc")
    planet = results[0]
    atmo = planet.properties["Atmosphere"]
    assert isinstance(atmo, dict)
    comp = atmo["Composition"]
    assert isinstance(comp, dict)
    assert comp["N2"] == "0.78"
    assert comp["O2"] == "0.21"


def test_parse_v2_backward_compat(bridge):
    """V2 파서가 기존 sample.sc (2단계)를 동일하게 파싱"""
    results = bridge.parse_sc_file_v2(FIXTURES / "sample.sc")
    names = [obj.name for obj in results]
    assert "MCP_TestStar" in names
    assert "MCP_TestPlanet" in names
    planet = next(o for o in results if o.name == "MCP_TestPlanet")
    assert planet.parent_body == "MCP_TestStar"


# ── to_sc 재귀 직렬화 ───────────────────────────────────────────────────────

def test_recursive_serialize_3level():
    """3단계 중첩 직렬화 → 파싱 라운드트립"""
    obj = CelestialObject(
        obj_type="Planet",
        name="RoundTrip",
        parent_body="Star",
        properties={
            "Mass": "1.0",
            "Surface": {
                "Style": "0.5",
                "Terrain": {
                    "HeightScale": "10",
                },
            },
        },
    )
    sc_text = obj.to_sc()
    assert "Surface" in sc_text
    assert "Terrain" in sc_text
    assert "HeightScale\t10" in sc_text


def test_moon_to_sc():
    """Moon 객체 직렬화 검증"""
    obj = CelestialObject(
        obj_type="Moon",
        name="TestMoon",
        parent_body="TestPlanet",
        properties={
            "Class": '"Selena"',
            "Mass": "0.012",
            "TidalLocked": "true",
            "Orbit": {"SemiMajorAxis": "0.00257", "Eccentricity": "0.055"},
        },
    )
    sc = obj.to_sc()
    assert 'Moon "TestMoon"' in sc
    assert 'ParentBody\t"TestPlanet"' in sc
    assert "TidalLocked\ttrue" in sc
    assert "Orbit" in sc


def test_nebula_to_sc():
    """Nebula 객체 직렬화 검증"""
    obj = CelestialObject(
        obj_type="Nebula",
        name="TestNebula",
        properties={"Type": '"Emission"', "Radius": "5.0", "Brightness": "1.5"},
    )
    sc = obj.to_sc()
    assert 'Nebula "TestNebula"' in sc
    assert "Radius\t5.0" in sc


def test_galaxy_to_sc():
    """Galaxy 객체 직렬화 검증"""
    obj = CelestialObject(
        obj_type="Galaxy",
        name="TestGalaxy",
        properties={"Type": '"Spiral"', "Radius": "15.0", "Mass": "5.0"},
    )
    sc = obj.to_sc()
    assert 'Galaxy "TestGalaxy"' in sc
    assert "Mass\t5.0" in sc


# ── Write 메서드 확장 ────────────────────────────────────────────────────────

def test_write_nebula_catalog(bridge, tmp_config):
    obj = CelestialObject("Nebula", "MCP_TestNebula", properties={"Radius": "5.0"})
    path = bridge.write_nebula_catalog([obj], catalog_name="TestNebula")
    assert path.exists()
    assert "nebulae" in str(path)


def test_write_galaxy_catalog(bridge, tmp_config):
    obj = CelestialObject("Galaxy", "MCP_TestGalaxy", properties={"Mass": "10.0"})
    path = bridge.write_galaxy_catalog([obj], catalog_name="TestGalaxy")
    assert path.exists()
    assert "galaxies" in str(path)


def test_search_all_catalog_dirs(bridge):
    """모든 카탈로그 디렉토리 검색 검증"""
    star = CelestialObject("Star", "MCP_SearchAll", properties={})
    nebula = CelestialObject("Nebula", "MCP_SearchAll_Nebula", properties={})
    bridge.write_star_catalog([star], catalog_name="SearchAll")
    bridge.write_nebula_catalog([nebula], catalog_name="SearchAll_Nebula")

    results = bridge.search_catalogs("SearchAll")
    names = [r.name for r in results]
    assert "MCP_SearchAll" in names
    assert "MCP_SearchAll_Nebula" in names


def test_list_catalogs_includes_nebulae(bridge):
    """list_addon_catalogs가 성운/은하 디렉토리도 포함"""
    obj = CelestialObject("Nebula", "MCP_ListTest", properties={})
    bridge.write_nebula_catalog([obj], catalog_name="ListTest")
    catalogs = bridge.list_addon_catalogs("nebulae")
    assert any(c["category"] == "nebulae" for c in catalogs)
