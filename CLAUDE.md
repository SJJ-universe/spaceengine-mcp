# SpaceEngine MCP — AI 컨텍스트 파일

SpaceEngine(우주 시뮬레이터)을 MCP를 통해 AI 에이전트가 제어할 수 있게 해주는 Python 서버 + Electron 프론트엔드.
외부 API 없이 **파일시스템 브릿지 + pywin32 콘솔 자동화**로 동작한다.

---

## 목차

1. [프로젝트 아키텍처](#1-프로젝트-아키텍처)
2. [금지 명령어 & 필수 규칙](#2-금지-명령어--필수-규칙)
3. [콘솔 자동화 규칙](#3-콘솔-자동화-규칙)
4. [SE 명령어 레퍼런스](#4-se-명령어-레퍼런스)
5. [SE 변수 레퍼런스](#5-se-변수-레퍼런스)
6. [SE 파일시스템 & 카탈로그](#6-se-파일시스템--카탈로그)
7. [명령어 화이트리스트](#7-명령어-화이트리스트)
8. [구현 상태 (68 Tools)](#8-구현-상태-68-tools)
9. [Frontend & LLM Provider](#9-frontend--llm-provider)
10. [개발 명령어](#10-개발-명령어)
11. [이슈 & 오류 이력](#11-이슈--오류-이력)
12. [상세 문서 링크](#12-상세-문서-링크)

---

## 1. 프로젝트 아키텍처

```
src/spaceengine_mcp/
  server.py         ← FastMCP 인스턴스 + register_tools() + Resources/Prompts
  models.py         ← 전체 Pydantic 모델
  api_layer.py      ← SSE용 REST 엔드포인트 (/health, /api/tools, /api/tools/execute)
  errors.py         ← MCPError 예외 계층 (SENotFoundError, ClipboardError 등)
  __main__.py       ← --transport stdio|sse --port 8765
  bridges/
    console_bridge.py   ← pywin32 콘솔 자동화 (핵심)
    script_bridge.py    ← .se 생성 + Run "mcp/파일.se" 실행
    catalog_bridge.py   ← .sc 읽기/쓰기 (재귀 파서 V2)
    log_bridge.py       ← se.log 파서 + 증분 읽기 + 상태 추출
    keyboard_bridge.py  ← F3/F9/모드 전환 키보드 입력
    config_bridge.py    ← main-user.cfg 읽기/쓰기
    state_bridge.py     ← 상태 모니터링 + 화면 캡처 + OCR
    flight_bridge.py    ← 비행 키 홀드 제어
  tools/
    phase1~11_*.py  ← Phase별 Tool 모듈 (register_tools 패턴)
frontend/               ← Electron + React 19 + Tailwind v4 + Zustand
  src/main/agent.ts        ← 대화 오케스트레이터 (Groq tool calling + Ollama Intent Parser 폴백)
  src/main/llm-providers.ts ← LLM Provider 추상화 (Groq/Gemini/Ollama 통합)
  src/main/mcp-client.ts   ← MCP HTTP 클라이언트 (timeout + retry)
```

---

## 2. 금지 명령어 & 필수 규칙

### 절대 사용 금지 명령어

| 잘못된 명령어 | 올바른 대체 | 설명 |
|---|---|---|
| `Camera` | `Goto` / `Center` / `GotoLocation` | Camera라는 독립 명령어는 존재하지 않음 |
| `SetDate` | `Date "YYYY.MM.DD hh:mm:ss"` | 점(.) 구분자 필수. 하이픈(-) 사용 불가 |
| `TimeRate` | `TimeScale` | 시간 속도 설정 |
| `Pause` | `StopTime` | 시간 일시정지 |
| `RealTime` | `StartTime` | 시간 재개 |
| `SetFOV` | `FOV 90` | Set 없이 FOV + 숫자 |
| `ExportScreenshot` | `Screenshot` | 스크린샷 촬영 |
| `MoveTo` | `Goto` | 카메라 이동 |
| `LookAt` | `Center` | 카메라 회전 |
| `TimeScale 0` | `StopTime` | TimeScale 0은 버그 유발! |
| `ESC` 키 | 틸드(0xC0) | ESC는 메인메뉴 이동 (콘솔 닫기 아님) |
| `Set "ShowGUI"` | `HideAllDialogs` + `HideAllToolbars` | ShowGUI는 SE에 존재하지 않는 변수 |
| `SetForce LandTargetRes` | `SetForce LandLODmaxRes` | 올바른 변수명 |
| `SetForce SolidResolution` | `SetForce FBOResolution` | 올바른 변수명 |

### 필수 규칙 6가지

1. **Goto/Orbit/Fly/Turn 후 반드시 Wait** — `Goto { Time 10 ... }` → `Wait 10` 필수. 없으면 다음 명령 즉시 실행
2. **TimeScale 0 금지** — 시간 정지는 `StopTime` 사용
3. **날짜 형식은 점(.) 구분** — `Date "2024.04.08 18:00:00"` (O) / `Date "2024-04-08"` (X)
4. **SaveVars/RestoreVars** — 스크립트 시작/끝에 항상 사용하여 설정 보호
5. **스크린샷 완료 대기** — `Screenshot` 후 `WaitTrigger "ScreenshotComplete"` 필수
6. **이름에 공백이 있으면 따옴표** — `Select "Alpha Centauri"`. 모호성 해소: `Select "Saturn|Pandora"`

### 천체 이름 규칙 (중요!)

SE는 내부 데이터베이스의 정확한 이름만 인식한다. 일반적으로 알려진 이름이 통하지 않을 수 있다.

| 일반 이름 | SE에서 사용되는 이름 (확인 필요) |
|-----------|-------------------------------|
| Proxima Centauri | `Proxima Cen` 또는 `Alpha Centauri C` |
| Andromeda Galaxy | `M 31` 또는 `Andromeda` |
| Orion Nebula | `M 42` |

- 공백 포함 이름은 반드시 따옴표로 감싸기: `Select "Alpha Centauri"`
- 동명 천체 구분: 부모|자식 형식 사용 — `Select "Saturn|Pandora"`
- **SE 실행 중 검색창(F3)에서 정확한 이름 확인 후 사용 권장**

---

## 3. 콘솔 자동화 규칙

### 제약사항

| 제약 | 이유 |
|------|------|
| **ESC 절대 금지** | SE에서 ESC = 메인메뉴 이동 (콘솔 닫기 아님) |
| **콘솔 토글 = 틸드(0xC0)** | 열기/닫기 모두 동일 키 |
| **모든 키 입력 = keybd_event** | SE는 DirectInput → WM_KEYDOWN 비신뢰 |
| **텍스트 = 클립보드 + keybd_event Ctrl+V** | keybd_event만 DirectInput에서 동작 |
| **SE 포그라운드 필수** | keybd_event는 포그라운드 창에 전달 |
| **카메라 잠금 해제 필수** | Scene1.se가 UserMoveControl "Disabled" 설정 |

### 카메라 잠금 해제 (navigate 전 필수)
```
UserMoveControl "Free"
UserRotationControl "Free"
UserTimeControl "Free"
```

### 스크립트 실행 방식 (2026-04-07 변경, 미검증)

**현재**: `Run "mcp/파일.se"` 명령으로 SE가 직접 스크립트 파일 실행
**경로**: `Run "파일명"` → `data/scripts/파일명.se` (상대경로, .se 자동 추가)
**MCP 스크립트 경로**: `data/scripts/mcp/` → `Run "mcp/파일명"`
**⚠️ 라이브 테스트 미완료!**

### 타이밍 설정 (console_bridge.py)

```
SetForegroundWindow 후:  0.7s
콘솔 열기 후:            1.0s
명령어 실행 후:          0.5s  (기본)
무거운 명령어 실행 후:   0.6s  (Goto, Run, SplinePath, Wait, Center, Land, SetFOV)
클립보드 붙여넣기 전후:  0.25s
Enter 전:               0.2s
```

---

## 4. SE 명령어 레퍼런스

### 카메라 제어

#### Select — 천체 선택
```
Select Earth
Select "Alpha Centauri"
Select "Saturn|Pandora"       // 부모|자식으로 모호성 해소
```

#### Goto — 선택 천체로 이동 (가장 중요!)
```
Goto                                     // 기본값(Time 2, DistRad 2)
Goto { Time 5 DistRad 3 }               // 5초, 반경 3배 거리
Goto { Time 0 }                          // 즉시 텔레포트
Goto { Time 10 DistKm 500 }             // 500km 거리
Goto { Time 8 Lon 86.4 Lat 13.5 HeightKm 150 }  // 좌표 위 150km
```
**Goto 전체 파라미터:** Time, AccelTime/DecelTime/DriftTime, Dist(pc)/DistKm/DistRad(기본2)/HeightKm, Lon/Lat, Yaw/Pitch/Roll, Up, Center false

#### Center / Horizon / Follow / Free / Track
```
Center { Time 5 }      // 카메라 회전만 (이동 없음)
Horizon { Time 3 }     // 지평선 방향
Follow                 // 천체 중심 추적(회전 무시)
SyncRot                // 표면 고정(회전 포함)
Free                   // 바인딩 해제
Track / Untrack        // 트래킹
```

#### FOV / Speed / MoveMode
```
FOV 90
MoveMode 1   // Free (관성 없음)
MoveMode 2   // Spacecraft (관성 있음)
Speed 2.5    // pc/s
SpeedKm 500  // km/s
```

#### Orbit — 선택 천체 주위 공전
```
Orbit { AngularSpeed 10 Axis (0, 1, 0) FadeTime 2 Func "Cubic" }
StopOrbit { FadeTime 2 }
```
Func: "Linear", "Quadric", "Cubic", "Sin"

#### Fly / Turn — 카메라 이동/회전
```
Fly { SpeedKm 500 FadeTime 2 Func "Cubic" }
StopFly { FadeTime 1.5 }
Turn { AngularSpeed 15 Axis (0, 1, 0) FadeTime 2 }
StopTurn { FadeTime 1.5 }
```

### 스플라인 카메라 경로

```
SplinePath "MyPath"
{
    Body       "Earth"
    Parent     "Sol"
    SyncRot    true
    Duration   30.0
    PosSpline  "Catmull-Rom"
    RotSpline  "B-spline"
    SplineData
    {
        // (time, pos.x, pos.y, pos.z, rot.w, rot.x, rot.y, rot.z)
        (0.000, 1.2e-7, 5.6e-8, 3.4e-7, 0.707, 0.0, 0.707, 0.0)
        (1.000, 3.4e-7, 7.8e-8, 5.6e-7, 0.707, 0.0, 0.707, 0.0)
    }
}
Select "MyPath"
Goto "MyPath"
Wait 3
PlaySplinePath "MyPath"
Wait 30    // Duration과 동일!
```

### 시간 제어
```
Date "2024.04.08 18:00:00"   // 점(.) 구분! 밀리초 가능
Date "current"               // 시스템 시계
TimeScale 100                // 100배속
TimeScale -100               // 역방향
StopTime                     // 일시정지 (TimeScale 0 대신!)
StartTime                    // 재개
```

### 표시 제어
```
Show Orbits              // 궤도선
Hide Clouds              // 구름
Show Constellations      // 별자리
FadeOut { Time 2 Color (0, 0, 0) }
FadeIn { Time 2 }
HideObject "Mars"
ShowObject "Jupiter|Io" { Time 3 }
```
Show/Hide 가능한 값: Planets, Stars, Clusters, Nebulae, Galaxies, Atmospheres,
Clouds, Water, Aurora, CometTails, Orbits, Constellations, Labels, Markers,
NightLights, Eclipses, PlanetShine, LensFlares, Grids, EclipseMask, Vectors

### 스크린샷 (WaitTrigger 필수!)
```
Screenshot
Screenshot { GUI false Format "png" Name "myshot" Path "screenshots/tour/" }
WaitTrigger "ScreenshotComplete"   // 반드시!
```

### UI/메시지
```
Print "Hello" { Time 10 Color (1, 1, 1, 1) PosX 0.5 PosY 0.1 AlignX "center" }
HidePrint
ShowMessage "Non-blocking"
WaitMessage "Blocking — Next 버튼 대기"
HideMessage
ShowDialog "Settings" { Tab "graphics" }
HideAllDialogs
HideAllToolbars
```

### 스크립트 / 조건문 / 트리거
```
Run "filename"              // data/scripts/filename.se 실행 (최대 16중첩)
Break                       // 스크립트 중단
Wait 5                      // 5초 대기

if { TimeScale > 100 }      // 조건문 (중첩 불가!)
    Set TimeScale 100
elif { TimeScale < 1 }
    Set TimeScale 1
endif

WaitTrigger "LoadingComplete"
WaitTrigger "ScreenshotComplete"
WaitTrigger "Object|Select" { Object "Earth" }
WaitTrigger "Object|Approach" { Object "Mars" RangeRad (1.5, 3.0) }
```

### 사용자 제어 제한
```
UserMoveControl "disabled" / "free"
UserMoveControl "limited" { Center "Mars" DistRad 5 SpeedKm 500 }
UserRotationControl "disabled" / "free"
UserTimeControl "disabled" / "free"
```

### 웨이포인트
```
Waypoint "Marker 1"
{
    Parent "Earth"
    Visible true
    Shape "Circle"    // Circle/Triangle/Square/Diamond/Hexagon/Billboard/Sphere
    Color (1, 0.8, 0, 0.6)
    RadiusKm 500
}
DeleteWaypoint "Marker 1"
ClearWaypoints
```

---

## 5. SE 변수 레퍼런스

### 변수 제어 명령어
```
Set LandLOD 1.0              // 범위 체크 O
SetForce BloomBright 0.7     // 모든 모드에 적용
Reset LandLOD                // 기본값 복원
Interpolate BloomBright { From 0 To 1 Time 3 Func "quadric" }
// Func: "linear", "quadric", "cubic", "sin", "exp", "revexp"
SaveVars / RestoreVars
```

### 성능/그래픽 변수 (정확한 이름!)

| 변수 | 타입 | 기본 | 범위 | 용도 |
|------|------|------|------|------|
| `QualityPreset` | int | 4 | 0~4 | 전체 품질 (0=최저, 4=울트라) |
| `LandLOD` | float | 0 | -1~1 | 지형 LOD |
| `LandLODmaxRes` | int | 1080 | 480~6480 | 지형 최대 해상도 |
| `FBOResolution` | float | 0.35 | 0.1~1 | 프레임버퍼 해상도 비율 |
| `MSAALevel` | int | 0 | 0~32 | MSAA 레벨 |
| `FXAA` | bool | true | — | FXAA |
| `AnisotropyLevel` | int | 0 | 0~16 | 이방성 필터링 |
| `BloomBright` | float | 0.7 | 0~1 | 블룸 밝기 |
| `MaxTilesPerFrame` | int | 8 | 1~20 | 프레임당 타일 로드 |
| `MaxTimePerFrame` | int | 8 | 1~100 | 프레임당 처리 시간 |
| `MaxThreads` | int | 10 | 1~10 | 최대 스레드 |
| `DrawClouds` | bool | true | — | 구름 렌더링 |
| `DrawWater` | bool | true | — | 물 렌더링 |
| `AuroraQuality` | int | 1 | 0~1 | 오로라 품질 |
| `BlackHoleQuality` | int | 2 | 0~3 | 블랙홀 품질 |
| `VSync` | int | 2 | 0~2 | 수직 동기화 |

### 영상/이미지 변수

| 변수 | 타입 | 기본 | 범위 |
|------|------|------|------|
| `ExposureComp` | float | 0 | -42~4 |
| `Brightness` | float | 1 | 0~2 |
| `Contrast` | float | 1 | 0~2 |
| `Saturation` | float | 1 | 0~2 |
| `Gamma` | float | 1 | 0~2 |
| `Sharpness` | float | 0 | 0~2 |

### ⚠️ 존재하지 않는 변수 (사용 금지!)

| 잘못된 변수명 | 올바른 변수명 | 오류 메시지 |
|---|---|---|
| `ShowGUI` | 없음 (→ `HideAllDialogs` + `HideAllToolbars` 사용) | `ERROR: 변수 불명: "ShowGUI"` |
| `LandTargetRes` | `LandLODmaxRes` | `ERROR: 변수 불명: "LandTargetRes"` |
| `SolidResolution` | `FBOResolution` | `ERROR: 변수 불명: "SolidResolution"` |

---

## 6. SE 파일시스템 & 카탈로그

### 파일시스템 구조

```
SpaceEngine/
├── data/                           ← 기본 데이터 (수정 금지)
│   ├── catalogs/stars/*.sc
│   ├── catalogs/planets/*.sc
│   ├── scripts/*.se               ← Run "파일명" 검색 경로
│   └── Catalogs0980.pak
├── addons/                         ← 사용자 애드온 (높은 우선순위)
│   ├── catalogs/stars/*.sc
│   ├── catalogs/planets/*.sc
│   └── scripts/*.se
├── config/
│   ├── main-user.cfg               ← 모든 설정
│   └── save-user.cfg               ← 카메라 위치/시간
├── system/
│   ├── SpaceEngine.exe
│   └── se.log
└── screenshots/
```

### .sc 카탈로그 형식 (항성)
```
Star "MyStarName"
{
    RA 16 10 45       // 적경
    Dec -25 12 11     // 적위
    Dist 100.0        // 거리(pc)
    Class "G2V"
    MassSol 1.0
    RadSol 1.0
    Teff 5778
    Lum 1.0
}
```

### .sc 카탈로그 형식 (행성 상세)
```
Planet "MyEarth"
{
    ParentBody "MyStarName"
    Class "Terra"
    Mass 1.0
    Radius 6371
    Obliquity 23.4
    RotationPeriod 24
    Surface { seaLevel 0.5  snowLevel 0.85  BumpHeight 15 }
    Atmosphere { Model "Earth"  Height 100  Pressure 1.0  Greenhouse 33
                 Composition { N2 78  O2 21  Ar 0.93 } }
    Ocean { Height 5 }
    Clouds { Coverage 0.5 }
    Rings { InnerRadius 10000  OuterRadius 50000 }
    Orbit { SemiMajorAxis 1.0  Period 1.0  Eccentricity 0.017 }
}
```

### 객체 삭제
```
Remove "ObjectName"
Remove "PlanetName" { ParentBody "StarName" }
```

---

## 7. 명령어 화이트리스트

허용 (2026-04-08 공식 문서 기준 검증):

```
Navigation:  Select, Unselect, Goto, Center, Horizon, GotoLocation, GotoURL
Binding:     Follow, SyncRot, Track, Untrack, Free
Camera:      FOV, MoveMode, Speed, SpeedKm, Fly, StopFly, Turn, StopTurn, Orbit, StopOrbit
User Ctrl:   UserMoveControl, UserRotationControl, UserTimeControl, UserStereobaseControl
Time:        Date, Time, TimeScale, StopTime, StartTime
Visibility:  Show, Hide, Toggle, ShowObject, HideObject, FadeOut, FadeIn
Interface:   Print, HidePrint, ShowMessage, WaitMessage, HideMessage,
             ShowDialog, HideDialog, HideAllDialogs, HideAllToolbars
Waypoints:   Waypoint, DeleteWaypoint, ClearWaypoints, GotoWaypoint
Splines:     SplinePath, PlaySplinePath, DeleteSplinePath, ClearSplinePaths
Variables:   SaveVars, RestoreVars, Set, SetU, SetForce, Reset, Interpolate
Flow:        Wait, WaitTrigger, WaitVar, Break, Loop, EndLoop,
             if, elif, else, endif, BeginMultiTrigger, EndMultiTrigger, CheckVersion
Sound:       PlaySound, StopSound, PlayMusic, PauseMusic, ResumeMusic
Script:      Run
Utility:     Screenshot, Log
삭제:        Remove
```

차단: Exit, Quit

---

## 8. 구현 상태 (68 Tools)

| Phase | Tools |
|-------|-------|
| 1+2 | navigate_to, run_script, search_catalog, create_star, create_planet, create_tour, set_time, toggle_overlay, list_addons, delete_addon |
| 3 | control_camera, take_screenshot, show_message, hide_message, toggle_gui, follow_object, read_log |
| 4 | play_sound, stop_sound, save_state, restore_state, create_flyby, create_comparison, set_rendering, wait_and_execute |
| 5 | set_variable, interpolate_variable, create_spline_path, manage_waypoints, camera_flight, set_speed, fade_effect, manage_dialogs, advanced_message |
| 6 | create_moon, create_barycenter, create_ring_system, edit_atmosphere, edit_surface, create_nebula, create_galaxy, search_catalog_v2 |
| 7 | record_video, search_object, hi_res_screenshot, switch_mode, keyboard_shortcut |
| 8 | edit_config, manage_addons, create_spacecraft, export_object_data |
| 9 | read_se_state, verify_command, screen_capture_ocr, smart_navigation |
| 10 | pilot_spacecraft, autopilot_control, docking_assist, flight_hud_read |
| 11 | cinematic_sequence, apply_preset, get_object_info, timelapse_capture, save_scene, load_scene, list_scenes, set_performance, restore_defaults |

### 성능 프리셋 (set_performance)

| 프리셋 | 설명 | 주요 설정 |
|--------|------|-----------|
| `potato` | 최저사양 | 구름/물 OFF, 모든 효과 최소 |
| `low` | 저사양 | FXAA만, 구름 OFF |
| `balanced` | 균형 (기본값) | FXAA + 구름/물 ON |
| `high` | 고사양 | MSAA 4x, 모든 효과 ON |
| `ultra` | 최고사양 | MSAA 8x, 모든 효과 최대 |
| `restore_defaults` | 기본값 복원 | RestoreVars + Reset |

---

## 9. Frontend & LLM Provider

### LLM Provider 지원 (3종)

| Provider | Tool Calling | 비용 | 기본값 |
|----------|-------------|------|--------|
| **Groq** (기본) | ✅ 지원 | 무료 (카드불필요) | llama-3.3-70b-versatile |
| Gemini | ✅ 지원 | 무료 250건/일 | gemini-2.0-flash |
| Ollama (로컬) | ❌ → Intent Parser 폴백 | 무료 | exaone3.5:7.8b |

- **Groq 기본 사용**: console.groq.com → API Key 발급 → LLM 설정에서 입력
- Agent는 LLMProvider 인터페이스를 통해 Provider를 런타임에 전환 가능
- Tool calling 지원 Provider → LLM이 직접 도구 호출 결정
- Tool calling 미지원 → Intent Parser(규칙 기반)로 폴백

---

## 10. 개발 명령어

```bash
# 의존성 설치
pip install -e ".[dev]"

# 단위 테스트 (189개)
pytest

# 라이브 테스트 (SE 실행 중 필요)
python test_send.py mars
python test_send.py saturn
python test_send.py tour
python test_send.py fade_out
python test_send.py set_var

# MCP 서버 (stdio — Claude Desktop)
python -m spaceengine_mcp

# MCP 서버 (SSE — Electron Frontend)
python -m spaceengine_mcp --transport sse --port 8765

# Frontend
cd frontend && npm run dev
cd frontend && npm test

# 점검
python scripts/check_ready.py
```

### 환경 변수

| 변수 | 기본값 |
|------|--------|
| `SE_INSTALL_PATH` | `C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine` |

---

## 11. 이슈 & 오류 이력

### 현재 미해결 이슈 (2026-04-08)

- **SE에서 명령어 미작동** — Run "mcp/파일.se" 방식 라이브 미검증 (가장 중요)
- **SplinePath 형식 불일치** — 코드에서 Knot 방식이나 SE 공식은 SplineData 방식
- ~~천체 이름 불일치~~ — ✅ 수정완료: `resolve_object_name()` 이름 매핑 + [SE 천체 이름 레퍼런스](docs/SE_OBJECT_NAMES.md)

### 해결된 이슈

| 오류 | 해결 |
|------|------|
| `변수 불명: "ShowGUI"` | ShowGUI는 존재하지 않는 변수 → `HideAllDialogs` + `HideAllToolbars` 사용 |
| `변수 불명: "LandTargetRes"` | `LandLODmaxRes`로 교체 |
| `변수 불명: "SolidResolution"` | `FBOResolution`으로 교체 |
| ESC로 메인메뉴 이동 | 틸드(0xC0)로 교체 |
| Camera 명령 사용 | Goto로 교체 |
| SetDate 사용 | Date "YYYY.MM.DD" 형식 |
| TimeScale 0 사용 | StopTime으로 교체 |
| {} 블록 깨짐 | Run "mcp/파일.se" 변경 |
| Interpolate Func 값 불일치 | "linear"/"quadric"/"cubic"/"sin"/"exp"/"revexp" 사용 |
| Intent Parser 천체이름 오류 | 네거티브 룩어헤드 |
| exaone tool calling 미지원 | Groq로 전환 + Intent Parser 폴백 |
| Quick Action 무한반복 | disabled + MCP 직접호출 |
| Screenshot WaitTrigger 누락 | `WaitTrigger "ScreenshotComplete"` 추가 |
| 천체 이름 불일치 (Proxima Centauri 등) | `resolve_object_name()` 자동 매핑 추가 |
| `Sirius\|B` 파이프 형식 오류 | SE 카탈로그 확인 → `"Sirius B"` (공백 형식) |

---

## 12. 상세 문서 링크

- [SE 천체 이름 레퍼런스](docs/SE_OBJECT_NAMES.md) — Catalogs.pak에서 추출한 실제 천체 이름 (스크립트 작성 시 참고!)
- [SE 스크립트 완전 레퍼런스](SE_SCRIPT_REFERENCE_FOR_CLAUDE_MD.md)
- [콘솔 자동화 규칙](docs/CONSOLE_RULES.md)
- [테스트 플레이 가이드](docs/TEST_PLAY_GUIDE.md)
- [프론트엔드 로드맵](docs/FRONTEND_ROADMAP.docx)
