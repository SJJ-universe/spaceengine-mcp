  
**SpaceEngine MCP Server**

개발 로드맵 및 기능 갭 분석

*Development Roadmap & Feature Gap Analysis*

2026년 4월 6일 | v0.1.0

# **1\. 현재 기능 커버리지 총괄**

SpaceEngine의 전체 기능 영역을 11개 카테고리로 분류하고, 현재 MCP 도구가 커버하는 비율을 분석한 결과입니다.

| 카테고리 | 상태 | MCP 도구 | 미커버 기능 |
| ----- | :---: | ----- | ----- |
| 탐색 / 내비게이션 | **✅ 완료** | navigate\_to, follow\_object | 검색(F3), 파라메트릭 검색 |
| 카메라 제어 | **⚠️ 부분** | control\_camera, create\_flyby | 스플라인 경로, Fly/Turn/Orbit |
| 시간 제어 | **✅ 완료** | set\_time | — |
| 천체 생성 / 카탈로그 | **⚠️ 부분** | create\_star, create\_planet | 상세 속성, 위성/고리/성운 생성 |
| 렌더링 / 시각화 | **⚠️ 부분** | toggle\_overlay, set\_rendering | Set 변수 직접 제어 |
| 스크린샷 / 비디오 | **⚠️ 부분** | take\_screenshot | 비디오 녹화, 고해상도 스크린샷 |
| 사운드 / 음악 | **✅ 완료** | play\_sound, stop\_sound | — |
| 투어 / 교육 | **✅ 완료** | create\_tour, create\_comparison | — |
| UI / 대화상자 | **⚠️ 부분** | toggle\_gui, show\_message | ShowDialog, 정보 패널 제어 |
| 상태 관리 / 변수 | **⚠️ 부분** | save\_state, restore\_state | Set/Get 변수, Interpolate |
| 비행 시뮬레이터 | **❌ 미구현** | — | 우주선 조종, 전체 비행 모드 |

**요약: 전체 11개 영역 중 완전 커버 4개, 부분 커버 6개, 미구현 1개. 콘솔 명령어로 수행 가능하지만 도구화되지 않은 기능이 상당수 존재합니다.**

# **2\. 콘솔 명령어의 한계**

현재 콘솔 명령어 방식으로는 SE의 모든 기능을 제어할 수 없습니다. 제어 방식별로 구분하면:

## **2.1 콘솔 명령어로 가능한 기능 (100%)**

| 기능 | 명령어 | 현재 도구화 |
| ----- | ----- | ----- |
| 천체 선택/이동 | Select, Goto, Center, Horizon | ✅ navigate\_to |
| 카메라 바인딩 | Follow, SyncRot, Track, Untrack, Free | ✅ follow\_object |
| 시간 제어 | Date, TimeScale, StopTime, StartTime | ✅ set\_time |
| 오버레이 표시 | Show, Hide, Toggle | ✅ toggle\_overlay |
| 화면 텍스트 | Print, HidePrint | ✅ show\_message |
| 스크린샷 | Screenshot | ✅ take\_screenshot |
| 사운드 | PlaySound, StopSound, PlayMusic | ✅ play\_sound |
| 상태 저장 | SaveVars, RestoreVars | ✅ save\_state |
| 카메라 거리/FOV | Goto { DistRad }, FOV | ✅ control\_camera |
| 변수 설정 | Set, SetForce, Reset, Interpolate | ❌ 미구현 |
| 스플라인 경로 | SplinePath, PlaySplinePath | ❌ 미구현 |
| 웨이포인트 | Waypoint, GotoWaypoint | ❌ 미구현 |
| 카메라 비행 | Fly, StopFly, Turn, StopTurn, Orbit | ❌ 미구현 |
| 다이얼로그 제어 | ShowDialog, HideDialog | ❌ 미구현 |
| 흐름 제어 | if/else, Loop, WaitTrigger | ❌ 미구현 |
| GUI 표시 | ShowGUI, HideGUI | ✅ toggle\_gui |
| 이동 속도 | Speed, SpeedKm | ❌ 미구현 |
| 페이드 효과 | FadeOut, FadeIn | ❌ 미구현 |

## **2.2 콘솔만으로는 불가능한 기능 (추가 방식 필요)**

| 기능 | 필요한 접근 방식 | 난이도 |
| ----- | ----- | ----- |
| 비디오 녹화 (F9) | pywin32 키보드 시뮬레이션 (F9, Ctrl+F9) | 중 |
| 고해상도 스크린샷 | SE 밌트인 대화상자 \+ pywin32 UI 자동화 | 중 |
| 천체 검색 (F3 창) | pywin32로 F3 누른 후 텍스트 입력 | 중 |
| 비행 시뮬레이터 모드 | pywin32 키보드 (1/2/3번 키 모드 전환) | 중∼고 |
| 우주선 조종 | pywin32 WASD \+ 물리 엔진 상호작용 | 고 |
| 설정 파일 수정 | config/main-user.cfg 직접 편집 | 하 |
| 애드온 설치/관리 | 파일시스템 작업 (addons/ 폴더) | 하 |
| Steam Workshop 연동 | Steam CLI 또는 API | 고 |
| VR 모드 제어 | SE VR 설정 \+ 전용 컨트롤러 API | 매우 고 |
| 현재 상태 읽기 | se.log 파싱 \+ 화면 OCR (pyautogui) | 중∼고 |
| 위성/고리/성운 생성 | .sc 카탈로그 확장 (Moon, Barycenter 태그) | 중 |
| 상세 행성 속성 | .sc 카탈로그 (Surface, Ocean, Rings, Atmosphere) | 중 |
| 우주선 정의 | .sss 파일 생성 \+ addons/models/ | 고 |

# **3\. 개발 로드맵**

우선순위와 난이도를 고려하여 6단계로 구성합니다. 각 Phase는 이전 Phase가 완료된 후 진행합니다.

## **Phase 5: 콘솔 명령어 완전 도구화**

목표: 이미 콘솔로 가능하지만 도구화되지 않은 기능을 MCP Tool로 노출

| 도구 | 기능 | 난이도 | 예상 기간 |
| ----- | ----- | ----- | ----- |
| set\_variable | Set/SetForce/Reset/Get 변수 제어 | 하 | 2일 |
| interpolate\_variable | Interpolate 변수 애니메이션 | 하 | 1일 |
| create\_spline\_path | SplinePath 정의 \+ PlaySplinePath 실행 | 중 | 3일 |
| manage\_waypoints | Waypoint CRUD \+ GotoWaypoint | 하 | 2일 |
| camera\_flight | Fly/Turn/Orbit 카메라 자유 비행 | 중 | 2일 |
| set\_speed | Speed/SpeedKm 이동 속도 설정 | 하 | 1일 |
| fade\_effect | FadeOut/FadeIn 화면 전환 효과 | 하 | 1일 |
| manage\_dialogs | ShowDialog/HideDialog 제어 | 하 | 1일 |
| advanced\_message | ShowMessage(BBCode)/WaitMessage 대화상자 | 하 | 1일 |

## **Phase 6: 카탈로그 확장 (.sc 고급)**

목표: .sc 카탈로그를 활용한 고급 천체 생성 및 편집

| 도구 | 기능 | 난이도 | 예상 기간 |
| ----- | ----- | ----- | ----- |
| create\_moon | Moon 태그로 위성 생성 | 중 | 2일 |
| create\_barycenter | Barycenter 태그로 쉘성계 생성 | 중 | 2일 |
| create\_ring\_system | Rings {} 블록으로 고리 생성 | 중 | 2일 |
| edit\_atmosphere | Atmosphere {} 상세 설정 (Composition, Pressure 등) | 중 | 3일 |
| edit\_surface | Surface {} 지형 상세 설정 (Terrain, Color) | 중 | 3일 |
| create\_nebula | Nebula 태그로 성운 생성 | 고 | 3일 |
| create\_galaxy | Galaxy 태그로 은하 생성 | 고 | 3일 |
| catalog\_parser\_v2 | 3단계+ 중첩 .sc 파서 개선 | 중 | 2일 |

## **Phase 7: pywin32 확장 (콘솔 외 기능)**

목표: 콘솔 명령어로 불가능한 기능을 pywin32 키보드/UI 자동화로 구현

| 도구 | 기능 | 방식 | 예상 기간 |
| ----- | ----- | ----- | ----- |
| record\_video | F9→설정→Ctrl+F9 녹화 시작/정지 | keybd\_event F9, Ctrl+F9 | 3일 |
| search\_object | F3 검색창 열고 텍스트 입력 | keybd\_event F3 \+ 클립보드 | 3일 |
| hi\_res\_screenshot | 고해상도 스크린샷 대화상자 조작 | pywin32 UI 자동화 | 4일 |
| switch\_mode | 탐색/비행 모드 전환 (1/2/3키) | keybd\_event 1/2/3 | 2일 |
| keyboard\_shortcut | 임의 키보드 단축키 전송 | keybd\_event 범용 | 2일 |

## **Phase 8: 파일시스템 브릿지 확장**

목표: SE 설정 파일 및 애드온 시스템 직접 조작

| 도구 | 기능 | 방식 | 예상 기간 |
| ----- | ----- | ----- | ----- |
| edit\_config | main-user.cfg 설정 읽기/수정 | 파일 I/O | 2일 |
| manage\_addons | 애드온 설치/제거/목록 | 파일시스템 | 3일 |
| create\_spacecraft | .sss 우주선 정의 파일 생성 | 템플릿 \+ 파일 I/O | 5일 |
| export\_object\_data | 천체 데이터 추출 (.sc 파싱) | 카탈로그 파서 | 2일 |

## **Phase 9: 인텔리전스 레이어**

목표: 에이전트가 SE 상태를 이해하고 자율적으로 판단할 수 있는 기반

| 도구 | 기능 | 방식 | 예상 기간 |
| ----- | ----- | ----- | ----- |
| read\_se\_state | se.log 실시간 모니터링 (선택된 천체, 위치, 오류) | log\_bridge 확장 | 3일 |
| verify\_command | 명령어 실행 후 결과 확인 (se.log 피드백) | log 파싱 \+ 대기 | 3일 |
| screen\_capture\_ocr | 화면 캡처 \+ OCR로 현재 상태 읽기 | pyautogui \+ Tesseract | 5일 |
| smart\_navigation | 문맥 인식 탐색 (거리·속도 자동 조정) | 로직 레이어 | 4일 |

## **Phase 10: 비행 시뮬레이터 통합 (장기)**

목표: 우주선 조종 및 전체 비행 시뮬레이터 모드 제어

| 도구 | 기능 | 난이도 | 예상 기간 |
| ----- | ----- | ----- | ----- |
| pilot\_spacecraft | WASD+시선 제어로 우주선 조종 | 매우 고 | 2주 |
| autopilot\_control | 오토파일릿 기능 제어 | 고 | 1주 |
| docking\_assist | 도킹 자동화 | 매우 고 | 2주 |
| flight\_hud\_read | 비행 HUD 정보 읽기 (OCR) | 고 | 1주 |

# **4\. 우선순위 및 예상 일정**

| Phase | 주제 | 예상 기간 | 핵심 성과 |
| ----- | ----- | ----- | ----- |
| **Phase 5** | 콘솔 명령어 완전 도구화 | \~2주 | 스플라인, 변수, 웨이포인트, 비행 명령 |
| **Phase 6** | 카탈로그 확장 | \~3주 | 위성, 고리, 성운, 대기/지형 상세 설정 |
| **Phase 7** | pywin32 확장 | \~2주 | 비디오, 검색, 모드 전환, 고해상도 스크린샷 |
| **Phase 8** | 파일시스템 브릿지 | \~2주 | 설정 파일, 애드온 관리, 우주선 정의 |
| **Phase 9** | 인텔리전스 레이어 | \~2주 | 상태 모니터링, 명령 검증, 스마트 탐색 |
| **Phase 10** | 비행 시뮬레이터 | \~6주 | 우주선 조종, 도킹, HUD 읽기 |

**총 예상 개발 기간: 약 17주 (Phase 5∼10 전체)**

Phase 5까지 완료하면 콘솔 명령어 기반 기능의 100% 도구화가 달성됩니다.

Phase 7까지 완료하면 콘솔 외 기능(비디오, 검색, 모드 전환)까지 커버됩니다.

Phase 10까지 완료하면 SE의 사실상 모든 기능을 AI가 제어할 수 있게 됩니다.

# **5\. 핵심 결론**

## **5.1 콘솔 명령어만으로 충분한가?**

아닙니다. 콘솔 명령어는 SE 전체 기능의 약 60%만 커버합니다. 나머지 40%를 커버하려면 3가지 추가 방식이 필요합니다:

* pywin32 키보드 시뮬레이션: 비디오 녹화(F9), 검색창(F3), 모드 전환(1/2/3), 고해상도 스크린샷 대화상자 등  
* 파일시스템 직접 조작: config/main-user.cfg 설정, .sss 우주선 정의, 애드온 설치/관리  
* 상태 모니터링: se.log 실시간 파싱, 화면 OCR, 명령어 실행 결과 검증

## **5.2 가장 효과적인 다음 단계는?**

Phase 5 (콘솔 명령어 완전 도구화)가 가장 높은 ROI를 가집니다. 이미 콘솔에서 검증된 명령어들을 Tool로 감싸기만 하면 되므로 리스크가 낮고, 스플라인 경로와 변수 제어는 시네마틱 활용도를 크게 높입니다.

## **5.3 아키텍처 확장 필요성**

현재 console\_bridge.py 한 개로 모든 입력을 처리하고 있습니다. Phase 7 이후부터는 다음과 같은 구조 확장이 필요합니다:

* KeyboardBridge: 콘솔 외 키보드 입력 전담 (F3, F9, 모드 전환 등)  
* ConfigBridge: SE 설정 파일 (.cfg) 읽기/쓰기  
* StateBridge: se.log \+ OCR 기반 상태 모니터링  
* FlightBridge: 비행 시뮬레이터 전용 제어 (WASD \+ 물리 엔진)

이 브릿지 확장은 Phase 7부터 점진적으로 적용하면 됩니다. Phase 5∼6은 현재 아키텍처 그대로 진행 가능합니다.