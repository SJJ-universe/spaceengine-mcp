"""SE 키바인딩 액션 이름을 콘솔에서 테스트"""
import time
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

# keys.cfg에서 발견한 정확한 액션 이름
TESTS = [
    'ToggleAtmospheres',     # keys.cfg: Shift-A
    'ToggleClouds',          # keys.cfg: Shift-C
    'ToggleOrbits',          # keys.cfg: O (비교용 - 작동 확인)
]

print("=== 키 액션 이름 콘솔 테스트 ===\n")
for cmd in TESTS:
    print(f"  전송: {cmd}")
    result = send_commands_via_console([cmd])
    time.sleep(1.5)

# 복원 (다시 토글해서 원래대로)
print("\n--- 복원 (재토글) ---")
for cmd in TESTS:
    print(f"  복원: {cmd}")
    result = send_commands_via_console([cmd])
    time.sleep(1.0)

print("\n완료. SE 콘솔에서 ERROR 확인 필요.")
