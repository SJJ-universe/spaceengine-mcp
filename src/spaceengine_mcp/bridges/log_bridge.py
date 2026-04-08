"""
SpaceEngine 로그 파서.

se.log 파일을 파싱하여 실행 상태, 오류, 로딩 진행 등을 모니터링한다.
"""
import re
from pathlib import Path
from datetime import datetime


def _parse_log_line(line: str) -> dict | None:
    """단일 로그 줄을 파싱하여 구조화된 dict 반환."""
    line = line.strip()
    if not line:
        return None

    entry: dict = {"raw": line}

    # 타임스탬프 패턴: [HH:MM:SS] 또는 HH:MM:SS
    m = re.match(r"\[?(\d{2}:\d{2}:\d{2})\]?\s*(.*)", line)
    if m:
        entry["time"] = m.group(1)
        entry["message"] = m.group(2)
    else:
        entry["message"] = line

    # 레벨 감지
    msg_lower = entry["message"].lower()
    if "error" in msg_lower or "exception" in msg_lower:
        entry["level"] = "error"
    elif "warning" in msg_lower or "warn" in msg_lower:
        entry["level"] = "warning"
    elif "fail" in msg_lower or "crash" in msg_lower:
        entry["level"] = "error"
    else:
        entry["level"] = "info"

    return entry


class LogBridge:
    """se.log 파서 브릿지 — 편의 클래스"""

    def __init__(self, log_path: Path):
        self.log_path = log_path

    def tail(self, lines: int = 50) -> list[dict]:
        return parse_log_tail(self.log_path, lines)

    def search(self, pattern: str, max_results: int = 20) -> list[dict]:
        return search_log(self.log_path, pattern, max_results)

    def errors(self, max_results: int = 30) -> list[dict]:
        return get_log_errors(self.log_path, max_results)

    def stats(self) -> dict:
        return get_log_stats(self.log_path)

    def selected_object(self) -> str | None:
        return get_selected_object(self.log_path)

    def camera_info(self) -> dict | None:
        return get_camera_info(self.log_path)

    def incremental(self, last_line: int = 0) -> tuple[list[dict], int]:
        return get_incremental_entries(self.log_path, last_line)


def parse_log_tail(log_path: Path, lines: int = 50) -> list[dict]:
    """se.log 파일의 마지막 N줄을 파싱하여 구조화된 로그 항목 반환."""
    if not log_path.exists():
        return []

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    raw_lines = text.splitlines()[-lines:]
    entries = []
    for line in raw_lines:
        entry = _parse_log_line(line)
        if entry:
            entries.append(entry)
    return entries


def search_log(log_path: Path, pattern: str, max_results: int = 20) -> list[dict]:
    """se.log에서 패턴(정규식)과 일치하는 줄을 검색."""
    if not log_path.exists():
        return []

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for i, line in enumerate(text.splitlines()):
        if regex.search(line):
            entry = _parse_log_line(line)
            if entry:
                entry["line_number"] = i + 1
                results.append(entry)
            if len(results) >= max_results:
                break
    return results


def get_log_errors(log_path: Path, max_results: int = 30) -> list[dict]:
    """se.log에서 오류/경고 메시지만 추출."""
    return search_log(log_path, r"(error|warning|fail|exception|crash)", max_results)


def get_log_stats(log_path: Path) -> dict:
    """se.log 전체 통계 (줄 수, 오류 수, 경고 수, 크기)."""
    if not log_path.exists():
        return {"exists": False}

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"exists": True, "readable": False}

    lines = text.splitlines()
    error_count = sum(1 for l in lines if re.search(r"error", l, re.IGNORECASE))
    warning_count = sum(1 for l in lines if re.search(r"warning", l, re.IGNORECASE))

    return {
        "exists": True,
        "readable": True,
        "total_lines": len(lines),
        "errors": error_count,
        "warnings": warning_count,
        "size_kb": round(log_path.stat().st_size / 1024, 1),
    }


# ── Phase 9 확장 함수 ────────────────────────────────────────────────────────

def get_selected_object(log_path: Path) -> str | None:
    """se.log에서 가장 최근에 선택된 천체 이름 추출"""
    if not log_path.exists():
        return None
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # SE 로그에서 "Selected: XXX" 또는 "Select XXX" 패턴 역순 검색
    for line in reversed(text.splitlines()):
        m = re.search(r'(?:Selected|Select)[:\s]+"?([^"]+?)"?\s*$', line)
        if m:
            return m.group(1).strip()
    return None


def get_camera_info(log_path: Path) -> dict | None:
    """se.log에서 카메라 관련 정보 추출 (위치, FOV 등)"""
    if not log_path.exists():
        return None
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    info: dict = {}
    for line in reversed(text.splitlines()):
        # FOV 정보
        m = re.search(r"FOV[:\s]+([\d.]+)", line)
        if m and "fov" not in info:
            info["fov"] = float(m.group(1))
        # DistRad 정보
        m = re.search(r"DistRad[:\s]+([\d.eE+-]+)", line)
        if m and "dist_rad" not in info:
            info["dist_rad"] = float(m.group(1))
        if len(info) >= 2:
            break
    return info if info else None


def get_incremental_entries(
    log_path: Path, last_line: int = 0
) -> tuple[list[dict], int]:
    """마지막으로 읽은 줄 번호 이후의 새 로그 항목만 반환.

    Returns:
        (new_entries, new_last_line): 새 항목 리스트와 업데이트된 줄 번호
    """
    if not log_path.exists():
        return [], last_line
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], last_line
    all_lines = text.splitlines()
    new_lines = all_lines[last_line:]
    entries = []
    for line in new_lines:
        entry = _parse_log_line(line)
        if entry:
            entries.append(entry)
    return entries, len(all_lines)