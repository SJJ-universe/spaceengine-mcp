# SpaceEngine MCP 프로젝트 현황

**최종 업데이트:** 2026-04-06
**프로젝트 경로:** `C:\Users\SJ\Desktop\spaceengine-mcp\`
**SpaceEngine 설치 경로:** `C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine`

---

## 아키텍처 요약

SE에 외부 REST/WebSocket API가 없으므로 **파일시스템 브리지 + pywin32 콘솔 자동화** 방식 사용.

```
FastMCP 서버 (server.py)
  └─ ScriptBridge      .se 파일 생성 → 콘솔로 실행
  └─ CatalogBridge     .sc 카탈로그 파일 읽기/쓰기
  └─ ConsoleBridge     pywin32로 SE 인게임 콘솔 자동화
```

---

## 콘솔 브리지 핵심 제약사항

| 제약 | 이유 |
|------|------|
| **ESC 절대 금지** | SE에서 ESC = 메인메뉴 이동 |
| **콘솔 토글 = 틸드(0xC0, `)** | 열기/닫기 모두 동일 키 |
| **텍스트 입력 = 클립보드 + keybd_event Ctrl+V** | SE는 DirectInput → WM_KEYDOWN 무시 |
| **모든 키 입력 = keybd_event** | DirectInput 게임은 WM_KEYDOWN 비신뢰 |
| **SE 포그라운드 필수** | keybd_event는 포그라운드 창으로 전달 |

---

## 메인 메뉴 카메라 잠금 문제

- SE 시작 시 Scene1.se 자동 실행 → `UserMoveControl "Disabled"` / `UserRotationControl "Disabled"` / `UserTimeControl "Disabled"` 설정
- 이 상태에서 Goto 명령 → `"Camera movement is limited, ignoring Goto command"` 경고
- **해결:** 내비게이션 명령 앞에 카메라 잠금 해제 명령 선행 전송
  - `UserMoveControl "Free"` / `UserRotationControl "Free"` / `UserTimeControl "Free"`
- **⚠️ `StopScript`는 콘솔 명령이 아님!** .se 파일 내부에서만 유효, 콘솔에서 "명령 불명" 오류

---

## 명령어 화이트리스트 (2026-04-06 공식 문서 기준 검증 완료)

### 공식 확인된 명령어
| 카테고리 | 명령어 |
|----------|--------|
| User Control | UserMoveControl, UserRotationControl, UserTimeControl, UserStereobaseControl |
| Navigation | Select, Unselect, Goto, Center, Horizon, GotoLocation, GotoURL |
| Camera Binding | Follow, SyncRot, Track, Untrack, Free |
| Camera Movement | FOV, Speed, SpeedKm, Fly, StopFly, Turn, StopTurn, Orbit, StopOrbit |
| Waypoints | Waypoint, DeleteWaypoint, ClearWaypoints, GotoWaypoint |
| Spline Paths | SplinePath, PlaySplinePath, DeleteSplinePath, ClearSplinePaths |
| Time Control | Date (=Time), TimeScale, StopTime, StartTime |
| Flow Control | Wait, WaitTrigger, WaitVar, Break, Loop/EndLoop, if/elif/else/endif |
| Variables | SaveVars, RestoreVars, Set, SetU, SetForce, Reset, Interpolate |
| Visibility | Show, Hide, Toggle, ShowObject, HideObject, FadeOut, FadeIn |
| Interface | Print, HidePrint, ShowMessage, WaitMessage, HideMessage, ShowDialog, HideDialog, ShowGUI, HideGUI |
| Sound | PlaySound, StopSound, PlayMusic, PauseMusic, ResumeMusic |
| Script | Run (최대 16단계 중첩) |
| Utility | Screenshot, Log |

### 공식 문서에 없는 명령어 (제거됨)
| 명령어 | 대체 |
|--------|------|
| ~~Camera~~ | Goto { DistRad ... Time ... } 사용 |
| ~~SetDate~~ | Date "YYYY.MM.DD HH:MM:SS" 사용 |
| ~~TimeRate~~ | TimeScale 사용 |
| ~~Pause~~ | StopTime 사용 |
| ~~RealTime~~ | StartTime 또는 TimeScale 1 사용 |
| ~~LookAt~~ | Center 또는 Track 사용 |
| ~~Unfollow~~ | Free 사용 |
| ~~StopMusic~~ | PauseMusic 사용 |
| ~~AddWaypoint~~ | Waypoint "Name" { ... } 사용 |
| ~~StopSplinePath~~ | 공식 문서 확인 필요 |
| ~~RecordSplinePath~~ | 런타임 녹화용, 스크립트 비추 |

### 차단 명령어
| 명령어 | 이유 |
|--------|------|
| Exit, Quit | SE 종료 방지 |

---

## 콘솔 브리지 타이밍 설정 (현재)

```python
DELAY_FOREGROUND = 0.5       # SetForegroundWindow 후 대기
DELAY_CONSOLE_OPEN = 0.8     # 콘솔 열기 후 대기
DELAY_AFTER_COMMAND = 0.4    # 명령어 실행 후 대기
DELAY_CLIPBOARD_BEFORE = 0.15  # 클립보드 붙여넣기 전 대기
DELAY_CLIPBOARD_AFTER = 0.15   # 클립보드 붙여넣기 후 대기
DELAY_BEFORE_ENTER = 0.1      # Enter 전 대기
_clear_input backspace 횟수:  40회 (keybd_event)
```

---

## 테스트 현황 (2026-04-06 기준)

| 테스트 | 상태 | 비고 |
|--------|------|------|
| `Select "Mars"` | ✅ 성공 | 화성 정보 패널 표시 확인 |
| `Goto { DistRad 3.0 }` | ⬜ 재테스트 필요 | UserMoveControl 잠금 해제 방식으로 변경 |
| orbits_on | ⬜ 미테스트 | |
| time_fast | ⬜ 미테스트 | |
| tour | ⬜ 재테스트 필요 | tour.se.j2 수정됨 (ShowMessage→Print, 잠금해제 추가) |
| flyby | ⬜ 재테스트 필요 | flyby.se.j2 수정됨 (Camera→Goto, 잠금해제 추가) |
| 단위 테스트 전체 | ✅ 24/24 통과 | script_bridge 14, catalog_bridge 10 |

---

## 오류 해결 이력

| 오류 | 원인 | 해결 |
|------|------|------|
| `RunScript` 명령 불명 | SE 콘솔 미지원 | 파일 읽어 각 줄을 직접 전송 |
| ESC로 메인메뉴 이동 | ESC = 메인메뉴 | 틸드(0xC0)로 교체 |
| Ctrl+V 안 됨 | WM_KEYDOWN은 DirectInput 무시 | keybd_event 사용 |
| `Camera movement limited` | Scene1.se가 UserMoveControl "Disabled" 설정 | UserMoveControl "Free" 선행 전송 |
| `명령 불명: StopScript` | StopScript는 .se 전용, 콘솔 미지원 | UserMoveControl "Free" 등으로 교체 |
| pyproject.toml 파싱 오류 | TOML table로 작성 | 배열로 수정 |
| tour.se.j2에 RunScript | BLOCKED_COMMANDS 위반 | 주석으로 교체 |
| validate_commands가 // 거부 | 주석 처리 누락 | startswith("//") 예외 추가 |
| OrbitParams default_factory 실패 | semi_major_axis 기본값 없음 | 기본값 1.0 추가 |
| win32con.VK_OEM_3 없음 | win32con 미정의 | 원시값 0xC0 직접 사용 |
| **flyby.se.j2 Camera 명령** | **Camera 명령 공식 문서에 없음** | **Goto로 교체 (2026-04-06)** |
| **tour.se.j2 ShowMessage** | **콘솔에서 ShowMessage 대화상자 표시** | **Print로 교체 (2026-04-06)** |
| **tour/flyby 카메라 잠금** | **템플릿에 잠금 해제 누락** | **UserMoveControl 등 추가 (2026-04-06)** |
| **pywin32 의존성 누락** | **pyproject.toml에 미등록** | **pywin32>=300 추가 (2026-04-06)** |
| **오버레이 이름 맵 중복** | **script_bridge + server.py 각각 보유** | **통합 OVERLAY_NAME_MAP (2026-04-06)** |
| **Wait 타이밍 부족** | **Goto 완료 전 다음 명령 실행** | **Wait에 +1초 여유 추가 (2026-04-06)** |

---

## 구현된 MCP Tools

### Phase 1
| Tool | 설명 |
|------|------|
| `navigate_to` | 천체로 카메라 이동 (카메라 잠금 해제 자동 포함) |
| `run_script` | .se 명령어 리스트 직접 실행 |
| `search_catalog` | 커스텀 카탈로그 검색 |

### Phase 2
| Tool | 설명 |
|------|------|
| `create_star` | 커스텀 항성 생성 |
| `create_planet` | 커스텀 행성 생성 (궤도 파라미터 검증 추가) |
| `create_tour` | 교육용 투어 생성 및 실행 |
| `set_time` | 시뮬레이션 시간/속도 설정 (Date + TimeScale/StopTime/StartTime) |
| `toggle_overlay` | 오버레이 표시/숨김 |
| `list_addons` | 애드온 카탈로그 목록 |
| `delete_addon` | 커스텀 카탈로그 삭제 |

### Phase 3
| Tool | 설명 |
|------|------|
| `control_camera` | 카메라 줌/FOV 조정 (Goto + FOV) |
| `take_screenshot` | 스크린샷 캡처 |
| `show_message` / `hide_message` | 화면 텍스트 (Print / HidePrint) |
| `toggle_gui` | UI 표시/숨김 (ShowGUI / HideGUI) |
| `follow_object` | 천체 추적 (Follow/Track/Free/Untrack) |
| `read_log` | SE 로그 분석 |

### Phase 4
| Tool | 설명 |
|------|------|
| `play_sound` / `stop_sound` | 사운드 제어 |
| `save_state` / `restore_state` | SaveVars / RestoreVars |
| `create_flyby` | 근접 비행 (Goto 기반) |
| `create_comparison` | 천체 비교 투어 |
| `set_rendering` | 렌더링 설정 (Show/Hide/Toggle, 통합 이름 맵) |
| `wait_and_execute` | 지연 실행 |

---

## 다음 단계

- [ ] Goto 동작 재확인 (SE 켠 후 `python test_send.py mars`)
- [ ] tour / flyby 수정 후 라이브 테스트
- [ ] catalog_bridge.py regex 3단계 중첩 지원 개선
- [ ] console_bridge.py 명령어 실행 결과 확인 메커니즘 (se.log 모니터링)
- [ ] 에이전트 복합 시나리오 테스트 (시네마틱 촬영 워크플로)
