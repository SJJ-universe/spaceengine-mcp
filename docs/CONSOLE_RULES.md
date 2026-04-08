# SpaceEngine 콘솔 자동화 규칙

SE 인게임 콘솔을 pywin32로 자동화할 때 반드시 지켜야 할 규칙 모음.
이 규칙들은 실제 테스트를 통해 검증된 것이며, 어기면 명령이 무시되거나 SE가 오작동한다.

---

## 규칙 1: ESC 키 절대 사용 금지

**규칙:** console_bridge.py에서 VK_ESCAPE를 어떤 상황에서도 사용하지 말 것.

**Why:** SE에서 ESC는 콘솔을 닫는 키가 아니라 메인 메뉴로 이동하는 키다.
ESC 전송 시 사용자가 씬에서 메인 메뉴로 빠져나가고, 이후 모든 명령이 실패한다.

**How to apply:** 콘솔 열기/닫기 모두 `_toggle_console(hwnd)` — 틸드(0xC0) 사용.

```python
CONSOLE_KEY = 0xC0   # ` / ~ 키
# 콘솔 열기도, 닫기도 모두 이 키만 사용
_keybd_tap(CONSOLE_KEY)
```

---

## 규칙 2: 텍스트 입력은 클립보드 + keybd_event

**규칙:** SE 콘솔에 텍스트를 입력할 때 `win32api.keybd_event`로 Ctrl+V를 전송할 것.

**Why:** SE는 DirectInput 게임이라 WM_KEYDOWN 등 Windows 메시지 기반 키 입력을 무시한다.
클립보드에 텍스트를 설정한 후 keybd_event로 Ctrl+V를 주입해야 SE가 실제 키 입력으로 인식한다.

**How to apply:**
```python
win32clipboard.OpenClipboard()
win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
win32clipboard.CloseClipboard()
win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
win32api.keybd_event(ord('V'), 0, 0, 0)
# ... key up ...
```

SE가 포그라운드 윈도우인 상태에서만 keybd_event가 해당 창으로 전달된다.
따라서 명령 전송 전에 반드시 `SetForegroundWindow(hwnd)` 호출 필요.

---

## 규칙 3: 모든 키 입력은 keybd_event 사용

**규칙:** 틸드(콘솔 토글), Enter(명령 실행), Backspace(입력 지우기) 모두 `keybd_event` 사용.

**Why:** SE는 DirectInput 게임이므로 WM_KEYDOWN/WM_KEYUP 메시지 기반 입력이 비신뢰.
keybd_event는 OS 레벨에서 실제 키 입력을 시뮬레이션하므로 DirectInput에서도 동작.

**How to apply:**
```python
def _keybd_tap(vk: int, delay: float = 0.05):
    win32api.keybd_event(vk, 0, 0, 0)
    time.sleep(delay)
    win32api.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(delay)
```

---

## 규칙 4: 내비게이션 명령 전 카메라 잠금 해제 (UserMoveControl)

**규칙:** Select + Goto 등 카메라 이동 명령 전에 반드시 카메라 잠금 해제 명령을 먼저 전송할 것.

**Why:** SE 시작 시 메인 메뉴의 `Scene1.se`가 자동 실행되어 `UserMoveControl "Disabled"`,
`UserRotationControl "Disabled"`, `UserTimeControl "Disabled"`로 카메라를 잠근다.
이 상태에서 Goto를 보내면 `"Camera movement is limited, ignoring Goto command"` 경고와 함께 무시된다.

**⚠️ `StopScript`는 콘솔 명령이 아님!** .se 스크립트 파일 내에서만 유효하며,
콘솔에서 입력하면 `ERROR: 명령 불명: "StopScript"` 오류 발생.

**How to apply:** `build_navigation_commands()`의 UNLOCK_COMMANDS 사용:

```
UserMoveControl "Free"       ← 카메라 이동 잠금 해제
UserRotationControl "Free"   ← 카메라 회전 잠금 해제
UserTimeControl "Free"       ← 시간 제어 잠금 해제
Select "Mars"                ← 대상 선택
Goto { ... }                 ← 이동
```

---

## 타이밍 참고값 (console_bridge.py 현재 설정)

| 단계 | 대기 시간 |
|------|-----------|
| SetForegroundWindow 후 | 0.5s |
| 콘솔 열기(_toggle_console) 후 | 0.8s |
| 일반 명령어 실행 후 | 0.4s |
| 클립보드 붙여넣기 전후 | 0.15s |
