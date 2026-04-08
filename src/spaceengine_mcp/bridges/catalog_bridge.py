import re
from dataclasses import dataclass, field
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig

CATALOG_PREFIX = "MCP_"


@dataclass
class CelestialObject:
    """SpaceEngine 천체 객체 모델"""

    obj_type: str        # Star, Planet, Moon, Barycenter, Nebula, Galaxy 등
    name: str
    parent_body: str = ""
    properties: dict = field(default_factory=dict)

    def to_sc(self) -> str:
        """SpaceEngine .sc 형식으로 직렬화 (임의 깊이 중첩 지원)"""
        lines = [f'{self.obj_type} "{self.name}"', "{"]
        if self.parent_body:
            lines.append(f'\tParentBody\t"{self.parent_body}"')
        lines.extend(self._serialize_block(self.properties, indent=1))
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _serialize_block(props: dict, indent: int = 1) -> list[str]:
        """속성 dict를 .sc 블록 라인으로 재귀 직렬화"""
        tab = "\t" * indent
        lines = []
        for key, value in props.items():
            if isinstance(value, dict):
                lines.append(f"{tab}{key}")
                lines.append(f"{tab}{{")
                lines.extend(CelestialObject._serialize_block(value, indent + 1))
                lines.append(f"{tab}}}")
            else:
                lines.append(f"{tab}{key}\t{value}")
        return lines


class CatalogBridge:
    """SpaceEngine .sc 카탈로그 파일 읽기/쓰기 브릿지"""

    def __init__(self, config: SpaceEngineConfig):
        self.config = config

    # ── Parser V1 (하위호환, 2단계 중첩) ─────────────────────────────────────

    def parse_sc_file(self, filepath: Path) -> list[CelestialObject]:
        """
        .sc 파일을 파싱하여 CelestialObject 리스트 반환.
        V2 재귀 파서를 사용하므로 임의 깊이 중첩 지원.
        """
        return self.parse_sc_file_v2(filepath)

    # ── Parser V2 (재귀 하강, 임의 깊이 중첩) ─────────────────────────────────

    def parse_sc_file_v2(self, filepath: Path) -> list[CelestialObject]:
        """재귀 하강 파서로 .sc 파일 파싱 (3단계+ 중첩 지원)"""
        content = filepath.read_text(encoding="utf-8")
        tokens = self._tokenize(content)
        objects = []
        pos = 0
        while pos < len(tokens):
            tok_type, tok_val = tokens[pos]
            # 최상위 객체: TYPE "NAME" { ... }
            if tok_type == "WORD" and pos + 2 < len(tokens):
                next_type, next_val = tokens[pos + 1]
                if next_type == "STRING":
                    if pos + 2 < len(tokens) and tokens[pos + 2][0] == "LBRACE":
                        obj_type = tok_val
                        obj_name = next_val
                        props, end_pos = self._parse_block_recursive(tokens, pos + 3)
                        parent = props.pop("ParentBody", "").strip('"')
                        objects.append(
                            CelestialObject(
                                obj_type=obj_type,
                                name=obj_name,
                                parent_body=parent,
                                properties=props,
                            )
                        )
                        pos = end_pos
                        continue
            pos += 1
        return objects

    @staticmethod
    def _tokenize(content: str) -> list[tuple[str, str]]:
        """
        .sc 파일 내용을 토큰 리스트로 변환.
        토큰 종류: WORD, STRING, LBRACE, RBRACE, NUMBER
        """
        tokens = []
        i = 0
        n = len(content)
        while i < n:
            c = content[i]
            # 공백/줄바꿈 건너뛰기
            if c in (' ', '\t', '\r', '\n'):
                i += 1
                continue
            # 주석 (// 또는 #)
            if c == '/' and i + 1 < n and content[i + 1] == '/':
                while i < n and content[i] != '\n':
                    i += 1
                continue
            if c == '#':
                while i < n and content[i] != '\n':
                    i += 1
                continue
            # 문자열 리터럴
            if c == '"':
                j = i + 1
                while j < n and content[j] != '"':
                    if content[j] == '\\' and j + 1 < n:
                        j += 2
                    else:
                        j += 1
                tokens.append(("STRING", content[i + 1:j]))
                i = j + 1
                continue
            # 중괄호
            if c == '{':
                tokens.append(("LBRACE", "{"))
                i += 1
                continue
            if c == '}':
                tokens.append(("RBRACE", "}"))
                i += 1
                continue
            # 워드 (숫자, 식별자, 음수 포함)
            if c.isalnum() or c in ('_', '-', '+', '.'):
                j = i
                while j < n and content[j] not in (' ', '\t', '\r', '\n', '{', '}', '"'):
                    j += 1
                word = content[i:j]
                # 숫자인지 판별
                try:
                    float(word)
                    tokens.append(("NUMBER", word))
                except ValueError:
                    tokens.append(("WORD", word))
                i = j
                continue
            # 기타 문자 건너뛰기
            i += 1
        return tokens

    @staticmethod
    def _parse_block_recursive(
        tokens: list[tuple[str, str]], pos: int
    ) -> tuple[dict, int]:
        """
        재귀적으로 { ... } 블록 내부를 파싱하여 dict 반환.
        반환: (properties_dict, end_position)
        """
        props: dict = {}
        n = len(tokens)
        while pos < n:
            tok_type, tok_val = tokens[pos]
            # 블록 끝
            if tok_type == "RBRACE":
                return props, pos + 1
            # KEY VALUE 또는 KEY { ... }
            if tok_type == "WORD":
                key = tok_val
                if pos + 1 < n:
                    next_type, next_val = tokens[pos + 1]
                    if next_type == "LBRACE":
                        # 중첩 블록
                        sub_props, end_pos = CatalogBridge._parse_block_recursive(
                            tokens, pos + 2
                        )
                        props[key] = sub_props
                        pos = end_pos
                        continue
                    elif next_type in ("STRING", "NUMBER", "WORD"):
                        props[key] = next_val if next_type != "STRING" else f'"{next_val}"'
                        pos += 2
                        continue
                # 키만 있는 경우 (값 없이)
                props[key] = ""
                pos += 1
                continue
            # STRING이나 NUMBER가 키 위치에 온 경우 건너뛰기
            pos += 1
        return props, pos

    # ── 카탈로그 이름 관리 ────────────────────────────────────────────────────

    def _safe_catalog_name(self, name: str) -> str:
        """카탈로그 이름에 MCP_ 접두사 보장"""
        if not name.startswith(CATALOG_PREFIX):
            return f"{CATALOG_PREFIX}{name}"
        return name

    # ── 카탈로그 쓰기 ────────────────────────────────────────────────────────

    def _addons_stars_dir(self) -> Path:
        d = self.config.install_path / "addons" / "catalogs" / "stars"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _addons_planets_dir(self) -> Path:
        d = self.config.install_path / "addons" / "catalogs" / "planets"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _addons_nebulae_dir(self) -> Path:
        d = self.config.install_path / "addons" / "catalogs" / "nebulae"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _addons_galaxies_dir(self) -> Path:
        d = self.config.install_path / "addons" / "catalogs" / "galaxies"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _all_catalog_dirs(self) -> list[Path]:
        """모든 카탈로그 디렉토리 반환"""
        return [
            self._addons_stars_dir(),
            self._addons_planets_dir(),
            self._addons_nebulae_dir(),
            self._addons_galaxies_dir(),
        ]

    def write_star_catalog(
        self, objects: list[CelestialObject], catalog_name: str
    ) -> Path:
        """항성 카탈로그 .sc 파일 생성"""
        safe_name = self._safe_catalog_name(catalog_name)
        path = self._addons_stars_dir() / f"{safe_name}.sc"
        content = "\n\n".join(obj.to_sc() for obj in objects) if objects else ""
        path.write_text(content, encoding="utf-8")
        return path

    def write_planet_catalog(
        self, objects: list[CelestialObject], catalog_name: str
    ) -> Path:
        """행성 카탈로그 .sc 파일 생성"""
        safe_name = self._safe_catalog_name(catalog_name)
        path = self._addons_planets_dir() / f"{safe_name}.sc"
        content = "\n\n".join(obj.to_sc() for obj in objects) if objects else ""
        path.write_text(content, encoding="utf-8")
        return path

    def write_nebula_catalog(
        self, objects: list[CelestialObject], catalog_name: str
    ) -> Path:
        """성운 카탈로그 .sc 파일 생성"""
        safe_name = self._safe_catalog_name(catalog_name)
        path = self._addons_nebulae_dir() / f"{safe_name}.sc"
        content = "\n\n".join(obj.to_sc() for obj in objects) if objects else ""
        path.write_text(content, encoding="utf-8")
        return path

    def write_galaxy_catalog(
        self, objects: list[CelestialObject], catalog_name: str
    ) -> Path:
        """은하 카탈로그 .sc 파일 생성"""
        safe_name = self._safe_catalog_name(catalog_name)
        path = self._addons_galaxies_dir() / f"{safe_name}.sc"
        content = "\n\n".join(obj.to_sc() for obj in objects) if objects else ""
        path.write_text(content, encoding="utf-8")
        return path

    # ── 카탈로그 검색 ────────────────────────────────────────────────────────

    def search_catalogs(
        self, query: str, obj_type: str | None = None
    ) -> list[CelestialObject]:
        """모든 카탈로그 디렉토리에서 이름으로 검색"""
        results: list[CelestialObject] = []
        for d in self._all_catalog_dirs():
            if not d.exists():
                continue
            for sc_file in d.glob(f"{CATALOG_PREFIX}*.sc"):
                try:
                    objects = self.parse_sc_file(sc_file)
                    for obj in objects:
                        if query.lower() in obj.name.lower():
                            if obj_type is None or obj.obj_type == obj_type:
                                results.append(obj)
                except Exception:
                    continue
        return results

    def list_addon_catalogs(self, category: str = "all") -> list[dict]:
        """설치된 애드온 카탈로그 목록 반환"""
        catalogs = []
        dirs = {
            "stars": self._addons_stars_dir(),
            "planets": self._addons_planets_dir(),
            "nebulae": self._addons_nebulae_dir(),
            "galaxies": self._addons_galaxies_dir(),
        }
        for cat, d in dirs.items():
            if category not in ("all", cat):
                continue
            if not d.exists():
                continue
            for sc_file in d.glob("*.sc"):
                catalogs.append({"name": sc_file.stem, "category": cat, "path": str(sc_file)})
        return catalogs

    # ── 카탈로그 삭제 ────────────────────────────────────────────────────────

    def delete_catalog(self, catalog_name: str) -> bool:
        """MCP_ 접두사 카탈로그 삭제 (안전: MCP_ 접두사만 삭제 가능)"""
        safe_name = self._safe_catalog_name(catalog_name)
        deleted = False
        for d in self._all_catalog_dirs():
            path = d / f"{safe_name}.sc"
            if path.exists():
                path.unlink()
                deleted = True
        return deleted