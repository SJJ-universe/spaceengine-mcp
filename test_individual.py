"""개별 명령어 에러 확인 — 새 콘솔 로그에서 각 명령어 1개씩 테스트"""
import time
from spaceengine_mcp.bridges.console_bridge import send_commands_via_console

# 테스트할 핵심 명령어들 (의심스러운 것 위주)
TEST_COMMANDS = [
    # GUI 변형 시도
    ("HideGUI", ['HideGUI']),
    ("ShowGUI", ['ShowGUI']),
    ("Set ShowGUI false", ['Set "ShowGUI" false']),
    ("Set ShowGUI true", ['Set "ShowGUI" true']),
    
    # 시간 관련
    ("StopTime", ['StopTime']),
    ("StartTime", ['StartTime']),
    ("TimeScale 1", ['TimeScale 1']),
    
    # Print/HidePrint
    ("Print test", ['Print "test message" { Time 3 }']),
    ("HidePrint", ['HidePrint']),
    
    # 카메라 모드
    ("Follow (after Select)", ['Select "Earth"', 'Follow']),
    ("Free", ['Free']),
    ("Track (after Select)", ['Select "Earth"', 'Track']),
    ("Untrack", ['Untrack']),
    
    # Date
    ("Date set", ['Date "2024.04.08 12:00:00"']),
    
    # Goto + Wait
    ("Goto+Wait", ['Select "Earth"', 'Goto { Time 3 DistRad 4 }', 'Wait 3']),
    
    # Center
    ("Center", ['Select "Earth"', 'Center { Time 3 }']),
]

print(f"=== 개별 명령어 테스트 — {len(TEST_COMMANDS)}개 ===\n")

for name, cmds in TEST_COMMANDS:
    print(f"[{name}] 전송: {cmds}")
    result = send_commands_via_console(cmds)
    status = result.get("status", "unknown")
    print(f"  → {status} (count={result.get('count', 0)})")
    time.sleep(2)  # SE 콘솔에서 에러 표시 시간

print("\n=== 완료 — SE 콘솔에서 ERROR 확인 필요 ===")
