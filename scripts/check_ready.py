"""
테스트 플레이 준비 상태 점검 스크립트

실행: python scripts/check_ready.py
모든 항목이 ✓ 이면 테스트 플레이 가능.
"""
import sys
import json
import urllib.request
import subprocess
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PASS = "[OK]"
FAIL = "[!!]"
WARN = "[??]"

results = []


def check(name: str, ok: bool, detail: str = ""):
    status = PASS if ok else FAIL
    results.append((status, name, detail))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    return ok


# ── 1. SpaceEngine ────────────────────────────────────────────────────────
print("\n[SpaceEngine]")
try:
    import win32gui
    found = False
    def cb(hwnd, _):
        global found
        if "SpaceEngine" in win32gui.GetWindowText(hwnd) and win32gui.IsWindowVisible(hwnd):
            found = True
    win32gui.EnumWindows(cb, None)
    check("SpaceEngine 프로세스", found, "실행 중" if found else "실행 필요")
except ImportError:
    check("SpaceEngine 프로세스", False, "pywin32 미설치 (Windows 전용)")

se_path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
check("SE 설치 경로", se_path.exists(), str(se_path))

# ── 2. MCP 서버 ──────────────────────────────────────────────────────────
print("\n[MCP Server]")
try:
    resp = urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=3)
    data = json.loads(resp.read())
    check("MCP 서버 연결", data.get("status") == "ok", f"v{data.get('version')} / {data.get('tools_count')} tools")
except Exception as e:
    check("MCP 서버 연결", False, f"http://127.0.0.1:8765 접속 실패 — python -m spaceengine_mcp --transport sse --port 8765")

# ── 3. Ollama ─────────────────────────────────────────────────────────────
print("\n[Ollama LLM]")
try:
    resp = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
    data = json.loads(resp.read())
    models = [m["name"] for m in data.get("models", [])]
    check("Ollama 서버", True, f"{len(models)} 모델")
    has_model = len(models) > 0
    check("LLM 모델 설치됨", has_model, ", ".join(models[:5]) if models else "ollama pull exaone3.5:7.8b")
except Exception:
    check("Ollama 서버", False, "http://127.0.0.1:11434 접속 실패 — ollama serve 실행 필요")

# ── 4. Frontend ───────────────────────────────────────────────────────────
print("\n[Frontend]")
frontend_dir = Path(__file__).parent.parent / "frontend"
check("frontend/ 디렉토리", frontend_dir.exists())
check("node_modules", (frontend_dir / "node_modules").exists(), "없으면: cd frontend && npm install")
check("빌드 결과", (frontend_dir / "dist" / "main" / "index.js").exists(), "없으면: cd frontend && npx electron-vite build")

# ── 5. 백엔드 테스트 ─────────────────────────────────────────────────────
print("\n[Tests]")
check("pytest 설치", shutil.which("pytest") is not None)

# ── 요약 ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
total = len(results)
print(f"  결과: {passed}/{total} 통과" + (f", {failed} 실패" if failed else ""))

if failed == 0:
    print("  🚀 테스트 플레이 준비 완료!")
else:
    print("  ⚠  위 실패 항목을 해결한 후 다시 실행하세요.")
print("=" * 50)
