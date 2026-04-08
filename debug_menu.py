"""메인 메뉴 카메라 잠금 디버깅 스크립트"""
import sys
import time
from src.spaceengine_mcp.bridges.console_bridge import send_commands_via_console

step = sys.argv[1] if len(sys.argv) > 1 else "all"

UNLOCK = [
    'UserMoveControl "Free"',
    'UserRotationControl "Free"',
    'UserTimeControl "Free"',
]

if step == "unlock":
    # 1단계: 카메라 잠금 해제만
    r = send_commands_via_console(UNLOCK)
    print("Unlock:", r)

elif step == "nav":
    # 2단계: Select + Goto만 (잠금 이미 해제된 후)
    r = send_commands_via_console(['Select "Mars"', 'Goto { DistRad 3.0 Time 5.0 }'])
    print("Navigation:", r)

elif step == "slow":
    # 3단계: 잠금 해제 → 3초 대기 → Select + Goto
    r1 = send_commands_via_console(UNLOCK)
    print("Unlock:", r1)
    print("3초 대기중...")
    time.sleep(3)
    r2 = send_commands_via_console(['Select "Mars"', 'Goto { DistRad 3.0 Time 5.0 }'])
    print("Navigation:", r2)

elif step == "all":
    # 전체 시퀀스 (잠금 해제 + Select + Goto 한 번에)
    cmds = UNLOCK + ['Select "Mars"', 'Goto { DistRad 3.0 Time 5.0 }']
    r = send_commands_via_console(cmds)
    print("All:", r)
