"""
SE Catalogs.pak에서 Extended 카탈로그 JSON을 생성하는 스크립트.

HIPPARCOS.csv (112K)를 제외한 모든 .sc/.csv 파일에서
천체 이름을 추출하여 celestial-extended.json으로 저장한다.

Usage:
    python scripts/generate_extended_catalog.py
"""

import csv
import io
import json
import re
import zipfile
from pathlib import Path

SE_INSTALL = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
PAK_PATH = SE_INSTALL / "data" / "catalogs" / "Catalogs.pak"
OUTPUT = Path(__file__).parent.parent / "frontend" / "src" / "main" / "data" / "celestial-extended.json"
CORE_PATH = Path(__file__).parent.parent / "frontend" / "src" / "main" / "data" / "celestial-core.json"

# Core 카탈로그에 이미 있는 ID들 (중복 제거용)
def load_core_ids() -> set[str]:
    if not CORE_PATH.exists():
        return set()
    with open(CORE_PATH, encoding="utf-8") as f:
        core = json.load(f)
    # se_name을 소문자로 저장하여 매칭
    return {obj["se_name"].lower() for obj in core}

# 파일 경로 → 카테고리 매핑
def path_to_category(filepath: str) -> tuple[str, str]:
    """(category, subcategory)를 반환"""
    fp = filepath.lower()
    if "stars/" in fp:
        if "blackhole" in fp: return ("black_hole", "stellar")
        if "browndwarf" in fp: return ("star", "brown_dwarf")
        if "neutronstar" in fp: return ("star", "neutron_star")
        if "whitedwarf" in fp: return ("star", "white_dwarf")
        if "exoplanetssun" in fp: return ("star", "exoplanet_host")
        if "planemo" in fp: return ("star", "planemo")
        return ("star", "star")
    if "planets/" in fp:
        if "exoplanet" in fp and "suns" not in fp: return ("exoplanet", "exoplanet")
        if "asteroid" in fp: return ("solar_system", "asteroid")
        if "kuiper" in fp: return ("other", "kuiper_belt")
        if "comet" in fp: return ("other", "comet")
        if "blackhole" in fp: return ("black_hole", "companion")
        if "browndwarf" in fp: return ("exoplanet", "brown_dwarf_planet")
        if "neutronstar" in fp: return ("exoplanet", "pulsar_planet")
        if "whitedwarf" in fp: return ("exoplanet", "white_dwarf_planet")
        if "solarsys" in fp: return ("solar_system", "solar_system")
        if "moon" in fp: return ("solar_system", "moon")
        if "planemo" in fp: return ("other", "planemo")
        if "sagittarius" in fp: return ("black_hole", "sgr_a_system")
        return ("exoplanet", "exoplanet")
    if "nebulae/" in fp: return ("nebula", "nebula")
    if "galaxies/" in fp: return ("galaxy", "galaxy")
    if "clusters/" in fp: return ("cluster", "cluster")
    return ("other", "other")

# .sc 파일에서 천체 이름 추출
SC_NAME_RE = re.compile(
    r'^(?:Star|StarBarycenter|Planet|Moon|DwarfMoon|Asteroid|Comet|'
    r'Nebula|Galaxy|Cluster|Barycenter|Remove)\s+"([^"]+)"',
    re.MULTILINE
)

def parse_sc(content: str) -> list[str]:
    """sc 파일에서 천체 이름 목록을 추출"""
    return SC_NAME_RE.findall(content)

# .csv 파일에서 이름 추출
def parse_csv(content: str, filepath: str) -> list[str]:
    """csv 파일의 첫 번째 컬럼(Name)을 추출"""
    names = []
    reader = csv.reader(io.StringIO(content))
    for row in reader:
        if not row or row[0].startswith("#"):
            continue
        name = row[0].strip()
        if name and not name.startswith("//"):
            names.append(name)
    return names

def make_id(name: str) -> str:
    """이름을 slug ID로 변환"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9가-힣]+', '-', slug)
    slug = slug.strip('-')
    return slug[:80] if slug else "unknown"

def main():
    if not PAK_PATH.exists():
        print(f"ERROR: {PAK_PATH} not found. Is SpaceEngine installed?")
        return

    core_ids = load_core_ids()
    print(f"Core catalog: {len(core_ids)} se_names loaded")

    # HIPPARCOS와 Constellations 제외
    SKIP_FILES = {"stars/HIPPARCOS.csv", "stars/Constellations.cfg"}

    all_objects: list[dict] = []
    seen_names: set[str] = set()

    with zipfile.ZipFile(PAK_PATH, "r") as z:
        for filepath in sorted(z.namelist()):
            if filepath in SKIP_FILES:
                print(f"  SKIP {filepath}")
                continue
            if not (filepath.endswith(".sc") or filepath.endswith(".csv")):
                print(f"  SKIP {filepath} (not .sc/.csv)")
                continue

            content = z.read(filepath).decode("utf-8", errors="replace")
            category, subcategory = path_to_category(filepath)

            if filepath.endswith(".csv"):
                names = parse_csv(content, filepath)
            else:
                names = parse_sc(content)

            count = 0
            for name in names:
                name_lower = name.lower()
                # 중복 + Core에 이미 있는 것 제외
                if name_lower in seen_names or name_lower in core_ids:
                    continue
                seen_names.add(name_lower)

                # 첫 번째 이름만 사용 (별칭 제거)
                primary_name = name.split("/")[0].strip()

                obj = {
                    "id": make_id(primary_name),
                    "name": primary_name,
                    "se_name": name.split("/")[0].strip(),
                    "category": category,
                    "subcategory": subcategory,
                }
                all_objects.append(obj)
                count += 1

            print(f"  {filepath:55s} → {count:>5} new ({category}/{subcategory})")

    # ID 중복 해결
    id_counts: dict[str, int] = {}
    for obj in all_objects:
        oid = obj["id"]
        if oid in id_counts:
            id_counts[oid] += 1
            obj["id"] = f"{oid}-{id_counts[oid]}"
        else:
            id_counts[oid] = 0

    # 카테고리별 정렬
    cat_order = ["solar_system", "star", "exoplanet", "nebula", "galaxy", "black_hole", "cluster", "other"]
    all_objects.sort(key=lambda e: (
        cat_order.index(e["category"]) if e["category"] in cat_order else 99,
        e["name"]
    ))

    # 저장
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_objects, f, ensure_ascii=False, indent=1)

    # 통계
    cats: dict[str, int] = {}
    for obj in all_objects:
        cats[obj["category"]] = cats.get(obj["category"], 0) + 1

    print(f"\n=== Extended Catalog: {len(all_objects)} objects ===")
    for c in cat_order:
        print(f"  {c}: {cats.get(c, 0)}")
    print(f"\nSaved to: {OUTPUT}")

if __name__ == "__main__":
    main()
