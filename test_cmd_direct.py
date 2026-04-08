"""SE Atmosphere/Clouds 직접 명령어 테스트"""
import time
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

# SE 에러 메시지에서 Atmosphere가 '명령어'로 인식됨 → 직접 파라미터 테스트
TESTS = [
    'Atmosphere false',      # 대기 끄기
    'Atmosphere true',       # 대기 켜기
    'Clouds false',          # 구름 끄기
    'Clouds true',           # 구름 켜기
    'Follow',                # Follow만 (unfollow?)
    'Select',                # 선택 해제?
]

print("=== 직접 명령어 형식 테스트 ===\n")
for cmd in TESTS:
    print(f"  전송: {cmd}")
    result = send_commands_via_console([cmd])
    time.sleep(1.0)

print("\n완료. SE 콘솔 확인 필요.")
