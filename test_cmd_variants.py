"""SE 명령어 형식 테스트 — Atmosphere/Clouds/Unfollow의 올바른 구문 확인"""
import time
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

# 테스트할 명령어 후보들
CANDIDATES = [
    # --- Unfollow 대안 ---
    ('Follow ""', "빈 Follow로 추적 해제"),
    ('Select ""', "빈 Select로 선택 해제"),
    
    # --- Atmosphere 토글 대안 ---
    ('Toggle Atmosphere', "Toggle + Atmosphere"),
    ('Set { Atmosphere false }', "Set 블록 (false)"),
    ('Set { Atmosphere true }', "Set 블록 (true)"),
    
    # --- Clouds 토글 대안 ---
    ('Toggle Clouds', "Toggle + Clouds"),
    ('Set { Clouds false }', "Set 블록 (false)"),
    ('Set { Clouds true }', "Set 블록 (true)"),
]

print("=== SE 명령어 형식 테스트 ===\n")
for cmd, desc in CANDIDATES:
    print(f"  전송: {cmd:40s} ({desc})")
    result = send_commands_via_console([cmd])
    time.sleep(1.5)  # SE 응답 대기
    print(f"  결과: {result}\n")

print("\n✅ 모든 명령 전송 완료. SE 콘솔에서 ERROR 확인 필요!\n")
print("콘솔 열기 → 스크롤로 각 명령어 옆의 ERROR 유무 확인")
