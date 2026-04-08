"""log_bridge 단위 테스트"""
import pytest
from pathlib import Path

from spaceengine_mcp.bridges.log_bridge import (
    parse_log_tail,
    search_log,
    get_log_errors,
    get_log_stats,
)


@pytest.fixture
def log_file(tmp_path):
    """테스트용 로그 파일 생성"""
    log = tmp_path / "se.log"
    log.write_text(
        "2025-07-01 10:00:00 [INFO] SpaceEngine started\n"
        "2025-07-01 10:00:01 [INFO] Loading textures\n"
        "2025-07-01 10:00:02 [WARNING] Texture quality reduced\n"
        "2025-07-01 10:00:03 [ERROR] Failed to load addon xyz\n"
        "2025-07-01 10:00:04 [INFO] Navigation to Mars\n"
        "Normal line without timestamp\n",
        encoding="utf-8",
    )
    return log


def test_parse_log_tail_returns_entries(log_file):
    entries = parse_log_tail(log_file, lines=10)
    assert len(entries) == 6


def test_parse_log_tail_limit(log_file):
    entries = parse_log_tail(log_file, lines=2)
    assert len(entries) == 2


def test_parse_log_tail_nonexistent(tmp_path):
    entries = parse_log_tail(tmp_path / "nonexistent.log")
    assert entries == []


def test_search_log_pattern(log_file):
    results = search_log(log_file, "Mars")
    assert len(results) == 1
    assert "Mars" in results[0]["message"]


def test_search_log_regex(log_file):
    results = search_log(log_file, r"load(ing|ed)?")
    assert len(results) >= 2  # "Loading textures" + "Failed to load addon"


def test_get_log_errors(log_file):
    errors = get_log_errors(log_file)
    levels = {e["level"] for e in errors}
    assert "error" in levels or "warning" in levels


def test_get_log_stats(log_file):
    stats = get_log_stats(log_file)
    assert stats["exists"] is True
    assert stats["total_lines"] == 6
    assert stats["errors"] >= 1
    assert stats["warnings"] >= 1


def test_get_log_stats_nonexistent(tmp_path):
    stats = get_log_stats(tmp_path / "nonexistent.log")
    assert stats["exists"] is False
