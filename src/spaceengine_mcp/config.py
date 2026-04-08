from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class SpaceEngineConfig:
    """SpaceEngine 설치 경로 및 관련 디렉토리 설정"""

    install_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "SE_INSTALL_PATH",
                r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine",
            )
        )
    )

    @property
    def scripts_dir(self) -> Path:
        """MCP가 생성하는 스크립트 저장 경로"""
        d = self.install_path / "data" / "scripts" / "mcp"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def addons_stars_dir(self) -> Path:
        d = self.install_path / "addons" / "catalogs" / "stars"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def addons_planets_dir(self) -> Path:
        d = self.install_path / "addons" / "catalogs" / "planets"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def addons_nebulae_dir(self) -> Path:
        d = self.install_path / "addons" / "catalogs" / "nebulae"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def addons_galaxies_dir(self) -> Path:
        d = self.install_path / "addons" / "catalogs" / "galaxies"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def screenshots_dir(self) -> Path:
        return self.install_path / "screenshots"

    @property
    def log_file(self) -> Path:
        return self.install_path / "system" / "se.log"

    @property
    def executable(self) -> Path:
        return self.install_path / "system" / "SpaceEngine.exe"

    def validate(self) -> list[str]:
        """설치 경로 유효성 검사. 문제가 있으면 경고 메시지 리스트 반환."""
        warnings = []
        if not self.install_path.exists():
            warnings.append(f"SE 설치 경로가 존재하지 않음: {self.install_path}")
        if not self.executable.exists():
            warnings.append(f"SpaceEngine.exe를 찾을 수 없음: {self.executable}")
        return warnings


# 전역 기본 설정 인스턴스
default_config = SpaceEngineConfig()
