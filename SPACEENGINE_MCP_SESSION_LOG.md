# SpaceEngine MCP 개발 세션 로그

**날짜:** 2026-04-03
**프로젝트:** `C:\Users\SJ\Desktop\spaceengine-mcp\`
**SpaceEngine:** `C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine`

---

## 프로젝트 개요

Python FastMCP 기반 MCP(Model Context Protocol) 서버로, AI 에이전트(Claude)가 SpaceEngine(우주 시뮬레이터)을 제어할 수 있게 한다. SE에는 외부 API가 없으므로 **파일시스템 브리지 + pywin32 콘솔 자동화** 방식을 사용.

---

## 구현 파일 구조

```
spaceengine-mcp/
├── src/spaceengine_mcp/
│   ├── server.py           # FastMCP 서버 (Tools, Resources)
│   ├── config.py           # SE 경로 설정
│   └── bridges/
│       ├── console_bridge.py   # pywin32 콘솔 자동화 (핵심)
│       ├── script_bridge.py    # .se 스크립트 생성/실행
│       └── catalog_bridge.py   # .sc 카탈로그 파일 관리
├── templates/
│   └── tour.se.j2          # Jinja2 투어 스크립트 템플릿
├── tests/
│   ├── test_script_bridge.py   # 14개 단위 테스트 (통과)
│   └── test_catalog_bridge.py  # 10개 단위 테스트 (통과)
├── test_send.py            # 라이브 테스트 스크립트
├── pyproject.toml
└── CLAUDE.md               # AI 컨텍스트 파일
```

---

## MCP 서버 도구 목록

| Tool | 설명 |
|------|------|
| `navigate_to` | 천체로 카메라 이동 |
| `run_script` | .se 스크립트 실행 |
| `search_catalog` | 카탈로그 검색 |
| `create_star` | 커스텀 별 생성 |
| `create_planet` | 커스텀 행성 생성 |
| `create_tour` | 교육용 투어 생성 |
| `set_time` | 시뮬레이션 시간 설정 |
| `toggle_overlay` | 오버레이 토글 |
| `list_addons` | 애드온 목록 |
| `delete_addon` | 애드온 삭제 |

---

## 콘솔 브리지 최종 구현 (console_bridge.py)

### 핵심 제약사항

| 제약 | 이유 |
|------|------|
| **ESC 절대 금지** | SE에서 ESC = 메인메뉴 이동 (콘솔 닫기가 아님) |
| **콘솔 토글 = 틸드(0xC0, `)** | 열기/닫기 모두 동일 키 |
| **텍스트 입력 = 클립보드 + keybd_event** | SE는 DirectInput → WM_KEYDOWN 무시 |
| **SE 포그라운드 필요** | keybd_event 작동 조건 |

### 주요 함수

```python
CONSOLE_KEY = 0xC0   # ` / ~ 키

def _toggle_console(hwnd):
    """콘솔 열기/닫기 — 틸드 키만 사용"""
    _send_msg_key(hwnd, CONSOLE_KEY, delay=0.1)

def _paste_via_clipboard(text):
    """클립보드 경유 붙여넣기 (SE가 포그라운드여야 함)"""
    win32clipboard.OpenClipboard()
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    win32clipboard.CloseClipboard()
    win32api.keybd_event(VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('V'), 0, 0, 0)
    # key up ...

def send_commands_via_console(commands, close_console=True):
    """SE 콘솔로 명령어 전송"""
    hwnd = find_se_window()
    win32gui.SetForegroundWindow(hwnd)
    _toggle_console(hwnd)     # 열기
    for cmd in commands:
        _clear_input(hwnd)
        _paste_via_clipboard(cmd)  # 또는 WM_CHAR 폴백
        _press_enter(hwnd)
    if close_console:
        _toggle_console(hwnd)  # 닫기 (ESC 아님!)
```

---

## MAINMENU.CFG 문제와 해결

### 증상
```
WARNING: , line 1: Camera movement is limited, ignoring Goto command
```
콘솔 헤더: `스크립트 재생중: DATA/SCRIPTS/SCRIPTS.PAK/MENU/MAINMENU.CFG`

### 원인
SE 시작 시 MAINMENU.CFG가 자동 실행되어 카메라를 "Menu Moon 1.2"에 고정. Goto 명령을 무시함.

### 해결 (2026-04-03 적용)
`build_navigation_commands()`에서 `StopScript`를 첫 번째 명령으로 추가:
```python
commands = ["StopScript", f'Select "{safe_target}"', ...]
```
`ALLOWED_COMMANDS`에도 `"StopScript"` 추가.

---

## 오류 해결 이력

| 오류 | 원인 | 해결 |
|------|------|------|
| `pyproject.toml` 파싱 오류 | `[project.dependencies]`를 TOML 테이블로 작성 | `dependencies = [...]`를 `[project]` 섹션 내 배열로 수정 |
| `win32con.VK_OEM_3` 없음 | win32con에 상수 미정의 | 원시값 `0xC0` 직접 사용 |
| `subprocess.Popen([EXE, script])` | 실행 중인 SE 대신 새 인스턴스 실행 | pywin32 콘솔 자동화로 전환 |
| `RunScript` 명령 불명 오류 | SE 콘솔에서 RunScript 미지원 | .se 파일 읽어 각 줄 직접 전송 |
| Ctrl+V 작동 안 함 | WM_KEYDOWN은 DirectInput 게임이 무시 | `keybd_event` 사용 |
| ESC로 메인메뉴 이동 | SE에서 ESC = 메인메뉴 | 틸드(0xC0)로 교체 |
| Goto 무시 ("Camera limited") | MAINMENU.CFG 실행 중 | StopScript 선행 실행 |
| em dash 인코딩 오류 | Windows cp949 콘솔에서 `—` 처리 불가 | `—` → `-` 변경 |

---

## 테스트 현황 (2026-04-03 기준)

```bash
# 라이브 테스트 명령
cd C:\Users\SJ\Desktop\spaceengine-mcp
python test_send.py mars        # Select "Mars" + Goto — StopScript 적용 후 재테스트 필요
python test_send.py orbits_on   # 궤도 표시
python test_send.py time_fast   # 시간 배속
python test_send.py tour        # 교육 투어
```

| 테스트 | 상태 | 비고 |
|--------|------|------|
| `Select "Mars"` | ✅ 성공 | 화성 정보 좌측 패널 표시 확인 |
| `Goto { DistRad 3.0 }` | ⬜ 재테스트 필요 | StopScript 추가 후 미확인 |
| orbits_on | ⬜ 미테스트 | |
| time_fast | ⬜ 미테스트 | |
| tour | ⬜ 미테스트 | |
| 단위 테스트 전체 | ✅ 24/24 통과 | script_bridge 14, catalog_bridge 10 |

---

## 다음 단계

1. `python test_send.py mars` 재실행 → StopScript 적용 후 Goto 동작 확인
2. orbits_on → time_fast → tour 순서로 테스트 진행
3. 모든 테스트 통과 시 MCP 서버 정식 실행 테스트

---

## 참고

- **MCP 서버 실행:** `cd spaceengine-mcp && python -m spaceengine_mcp.server`
- **CLAUDE.md:** 프로젝트 AI 컨텍스트 파일 (아키텍처, 제약사항 상세 기록)
- SE 스크립트 디렉토리: `[SE설치경로]/data/scripts/mcp/`
- 카탈로그 디렉토리: `[SE설치경로]/data/catalogs/stars/` 등
