"""SE Show/Hide 파라미터 변형 최종 테스트"""
import time
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

# Show/Hide에 가능한 파라미터 변형
TESTS = [
    'Show Atmospheres',      # 복수형 (keys.cfg 패턴)
    'Hide Atmospheres',
    'Show Atmo',             # 약어
    'Hide Atmo',
    'Show Water',            # keys.cfg에 ToggleWater 있음
]

print("=== Show/Hide 파라미터 변형 테스트 ===\n")
for cmd in TESTS:
    print(f"  전송: {cmd}")
    result = send_commands_via_console([cmd])
    time.sleep(1.0)
print("\n완료.")
