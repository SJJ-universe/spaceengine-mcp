"""Clouds 변형 + Atmospheres 최종 확인"""
import time
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

TESTS = [
    'Show Atmospheres',   # 복수형 확인
    'Hide Atmospheres',   # 복수형 확인
    'Show Clouds',        # Clouds 원래 형식
    'Hide Clouds',        # Clouds 원래 형식
    'Follow',             # unfollow 확인
]

print("=== 최종 명령어 확인 ===\n")
for cmd in TESTS:
    print(f"  전송: {cmd}")
    result = send_commands_via_console([cmd])
    time.sleep(1.0)

# 복원
print("\n--- 복원 ---")
for cmd in ['Show Atmospheres', 'Show Clouds']:
    send_commands_via_console([cmd])
    time.sleep(0.5)

print("\n완료. 스크린샷으로 확인.")
