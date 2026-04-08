"""Phase 9 — StateBridge + log_bridge 확장 테스트"""
import pytest
import time
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.state_bridge import StateBridge
from spaceengine_mcp.bridges.log_bridge import (
    get_selected_object,
    get_camera_info,
    get_incremental_entries,
)


@pytest.fixture
def tmp_config(tmp_path):
    config = SpaceEngineConfig(install_path=tmp_path)
    # se.log 디렉토리 생성
    system_dir = tmp_path / "system"
    system_dir.mkdir(parents=True)
    return config


@pytest.fixture
def log_file(tmp_config):
    """샘플 로�� 파일 생성"""
    log_path = tmp_config.log_file
    log_path.write_text(
        "2026-04-07 09:00:00 Application started\n"
        "2026-04-07 09:00:01 Loading catalogs\n"
        'Select "Mars"\n'
        "2026-04-07 09:00:05 Selected: Mars\n"
        "2026-04-07 09:00:06 FOV: 45.0\n"
        "2026-04-07 09:00:07 TimeScale: 100.0\n"
        "2026-04-07 09:00:10 warning: texture not found\n",
        encoding="utf-8",
    )
    return log_path


@pytest.fixture
def bridge(tmp_config):
    return StateBridge(tmp_config)


# ── get_selected_object ───────���──────────��───────────────────────────────────

def test_get_selected_object(log_file):
    result = get_selected_object(log_file)
    assert result == "Mars"


def test_get_selected_object_missing_log(tmp_config):
    result = get_selected_object(tmp_config.log_file)
    assert result is None


# ── get_camera_info ────────────────────────────────��─────────────────────────

def test_get_camera_info(log_file):
    info = get_camera_info(log_file)
    assert info is not None
    assert info.get("fov") == 45.0


def test_get_camera_info_empty(tmp_config):
    """로그 없으면 None"""
    result = get_camera_info(tmp_config.log_file)
    assert result is None


# ── get_incremental_entries ─��────────────────────────────────────────────────

def test_incremental_read(log_file):
    # 처음 전체 읽기
    entries1, pos1 = get_incremental_entries(log_file, 0)
    assert len(entries1) > 0
    assert pos1 > 0

    # 같은 위치에서 다시 읽기 → 새 엔트리 없��
    entries2, pos2 = get_incremental_entries(log_file, pos1)
    assert len(entries2) == 0
    assert pos2 == pos1

    # 로그에 새 줄 추가
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("2026-04-07 09:01:00 New entry added\n")

    entries3, pos3 = get_incremental_entries(log_file, pos1)
    assert len(entries3) == 1
    assert "New entry" in entries3[0]["message"]
    assert pos3 > pos1


# ── StateBridge.get_current_state ───────────────���──────────────────────────���─

def test_get_current_state(bridge, log_file):
    state = bridge.get_current_state()
    assert state["selected_object"] == "Mars"
    assert isinstance(state["recent_errors"], list)
    assert "log_stats" in state


def test_get_current_state_no_log(bridge, tmp_config):
    """로그 파일 없을 때도 에러 없이 동작"""
    state = bridge.get_current_state()
    assert state["selected_object"] is None


# ── StateBridge.wait_for_log_entry ───────────��───────────────────────────────

def test_wait_for_log_entry_timeout(bridge, log_file):
    """패턴이 없으면 timeout 후 None"""
    result = bridge.wait_for_log_entry("NonExistentPattern12345", timeout=0.5, poll_interval=0.2)
    assert result is None
