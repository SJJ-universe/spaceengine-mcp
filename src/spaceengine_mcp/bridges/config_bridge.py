"""
SpaceEngine 설정 파일 브릿지 — config/main-user.cfg 읽기/쓰기.

SE 사용자 설정 파일은 KEY VALUE 형태의 간단한 텍스트 파일입니다.
수정 전 항상 .bak 백업을 생성합니다.
"""
import re
import shutil
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig


class ConfigBridge:
    """SE 설정 파일 (.cfg) 읽기/쓰기 브릿지"""

    def __init__(self, config: SpaceEngineConfig):
        self.config = config
        self.config_path = config.install_path / "config" / "main-user.cfg"

    def read_config(self) -> dict[str, str]:
        """main-user.cfg를 KEY→VALUE 딕셔너리로 파싱"""
        result: dict[str, str] = {}
        if not self.config_path.exists():
            return result
        for line in self.config_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                result[parts[0]] = parts[1]
            elif len(parts) == 1:
                result[parts[0]] = ""
        return result

    def get_value(self, key: str) -> str | None:
        """특정 설정 값 반환"""
        cfg = self.read_config()
        return cfg.get(key)

    def set_value(self, key: str, value: str) -> dict:
        """
        설정 값 수정. .bak 백업 후 파일 수정.
        키가 없으면 파일 끝에 추가.
        """
        if not self.config_path.exists():
            return {"status": "error", "message": f"설정 파일 없음: {self.config_path}"}

        # 백업 생성
        backup_path = self.config_path.with_suffix(".cfg.bak")
        shutil.copy2(self.config_path, backup_path)

        content = self.config_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        found = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("#"):
                parts = stripped.split(None, 1)
                if parts and parts[0] == key:
                    new_lines.append(f"{key} {value}")
                    found = True
                    continue
            new_lines.append(line)

        if not found:
            new_lines.append(f"{key} {value}")

        self.config_path.write_text("\n".join(new_lines), encoding="utf-8")
        return {
            "status": "ok",
            "key": key,
            "value": value,
            "backup": str(backup_path),
            "action": "updated" if found else "added",
        }

    def list_config(self) -> list[dict]:
        """모든 설정 항목을 리스트로 반환"""
        cfg = self.read_config()
        return [{"key": k, "value": v} for k, v in cfg.items()]
