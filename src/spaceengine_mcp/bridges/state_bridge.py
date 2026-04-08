"""
SpaceEngine 상태 모니터링 브릿지.

se.log 기반 상태 추적 + 화면 캡처 + OCR (선택적).
Phase 9 인텔리전스 레이어의 핵심 컴포넌트.
"""
import re
import time
from pathlib import Path

from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.log_bridge import (
    get_log_stats,
    get_log_errors,
    get_selected_object,
    get_camera_info,
    get_incremental_entries,
    search_log,
)


class StateBridge:
    """SE 상태 모니터링 브릿지"""

    def __init__(self, config: SpaceEngineConfig):
        self.config = config
        self.last_log_position: int = 0

    def get_current_state(self) -> dict:
        """현재 SE 상태를 종합 반환"""
        log_path = self.config.log_file
        stats = get_log_stats(log_path)
        selected = get_selected_object(log_path)
        camera = get_camera_info(log_path)
        recent_errors = get_log_errors(log_path, max_results=5)

        return {
            "selected_object": selected,
            "camera_info": camera,
            "recent_errors": [e["message"] for e in recent_errors],
            "log_stats": stats,
        }

    def wait_for_log_entry(self, pattern: str, timeout: float = 10.0, poll_interval: float = 0.5) -> dict | None:
        """
        se.log에서 패턴과 일치하는 새 엔트리가 나타날 때까지 대기.
        timeout 초과 시 None 반환.
        """
        log_path = self.config.log_file
        if not log_path.exists():
            return None

        # 현재 파일 끝 위치 기록
        start_pos = log_path.stat().st_size if log_path.exists() else 0
        regex = re.compile(pattern, re.IGNORECASE)
        elapsed = 0.0

        while elapsed < timeout:
            entries, new_pos = get_incremental_entries(log_path, start_pos)
            for entry in entries:
                if regex.search(entry["message"]):
                    return entry
            start_pos = new_pos
            time.sleep(poll_interval)
            elapsed += poll_interval

        return None

    def capture_screen(self) -> dict:
        """
        SE 창 스크린샷 캡처 (PIL/Pillow 사용).
        Pillow가 없으면 에러 반환.
        """
        try:
            from PIL import ImageGrab
        except ImportError:
            return {"status": "error", "message": "Pillow가 설치되지 않음. pip install Pillow"}

        try:
            from spaceengine_mcp.bridges.console_bridge import find_se_window
            import win32gui

            hwnd = find_se_window()
            if hwnd is None:
                return {"status": "error", "message": "SE 창을 찾을 수 없음"}

            rect = win32gui.GetWindowRect(hwnd)
            screenshot = ImageGrab.grab(bbox=rect)
            save_path = self.config.screenshots_dir / f"mcp_capture_{int(time.time())}.png"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot.save(str(save_path))

            return {"status": "ok", "path": str(save_path), "size": list(screenshot.size)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ocr_screen(self, region: tuple[int, int, int, int] | None = None) -> dict:
        """
        화면 캡처 + OCR 텍스트 추출.
        pytesseract가 없으면 에러 반환.
        """
        try:
            from PIL import ImageGrab
        except ImportError:
            return {"status": "error", "message": "Pillow가 설치되지 않음"}
        try:
            import pytesseract
        except ImportError:
            return {"status": "error", "message": "pytesseract가 설치되지 않음. pip install pytesseract"}

        try:
            from spaceengine_mcp.bridges.console_bridge import find_se_window
            import win32gui

            hwnd = find_se_window()
            if hwnd is None:
                return {"status": "error", "message": "SE 창을 찾을 수 없음"}

            rect = win32gui.GetWindowRect(hwnd)
            screenshot = ImageGrab.grab(bbox=rect)

            if region:
                screenshot = screenshot.crop(region)

            text = pytesseract.image_to_string(screenshot)
            return {"status": "ok", "text": text.strip(), "region": region}
        except Exception as e:
            return {"status": "error", "message": str(e)}
