"""Phase 8 — ConfigBridge 단위 테스트"""
import shutil
import pytest
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.config_bridge import ConfigBridge

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_config(tmp_path):
    """임시 경로에 설정 파일 복사"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    shutil.copy(FIXTURES / "main-user.cfg", config_dir / "main-user.cfg")
    return SpaceEngineConfig(install_path=tmp_path)


@pytest.fixture
def bridge(tmp_config):
    return ConfigBridge(tmp_config)


# ── read_config ──────────────────────────────────────────────────────────────

def test_read_config(bridge):
    cfg = bridge.read_config()
    assert "FullScreen" in cfg
    assert cfg["FullScreen"] == "false"
    assert cfg["ScreenWidth"] == "1920"


def test_read_config_skips_comments(bridge):
    cfg = bridge.read_config()
    # 주석 줄은 포함되지 않음
    assert not any(k.startswith("//") for k in cfg.keys())


# ── get_value ────────────────────────────────────────────────────────────────

def test_get_value_existing(bridge):
    assert bridge.get_value("VSync") == "true"


def test_get_value_missing(bridge):
    assert bridge.get_value("NonExistent") is None


# ── set_value ────────────────────────────────────────────────────────────────

def test_set_value_update_existing(bridge):
    result = bridge.set_value("ScreenWidth", "2560")
    assert result["status"] == "ok"
    assert result["action"] == "updated"
    # 값이 실제로 변경됨
    assert bridge.get_value("ScreenWidth") == "2560"


def test_set_value_adds_new_key(bridge):
    result = bridge.set_value("NewSetting", "42")
    assert result["status"] == "ok"
    assert result["action"] == "added"
    assert bridge.get_value("NewSetting") == "42"


def test_set_value_creates_backup(bridge):
    bridge.set_value("ScreenWidth", "2560")
    backup = bridge.config_path.with_suffix(".cfg.bak")
    assert backup.exists()
    # 백업에는 원래 값이 있음
    backup_content = backup.read_text(encoding="utf-8")
    assert "1920" in backup_content


# ── list_config ──────────────────────────────────────────────────────────────

def test_list_config(bridge):
    entries = bridge.list_config()
    assert len(entries) > 0
    assert all("key" in e and "value" in e for e in entries)
    keys = [e["key"] for e in entries]
    assert "StarBrightness" in keys
