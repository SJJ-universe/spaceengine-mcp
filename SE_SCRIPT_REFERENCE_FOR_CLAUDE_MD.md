# SpaceEngine 스크립트 완전 레퍼런스 (CLAUDE.md용)

> 이 파일의 내용을 프로젝트의 CLAUDE.md에 추가하면 AI가 정확한 SE 명령어만 사용합니다.

---

## 1. 절대 사용 금지 명령어

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

---

## 2. 필수 규칙 6가지

1. **Goto/Orbit/Fly/Turn 후 반드시 Wait** — `Goto { Time 10 ... }` 다음에 `Wait 10` 필수. 안 하면 다음 명령이 즉시 실행됨.
2. **TimeScale 0 금지** — 시간 정지는 `StopTime` 사용. `TimeScale 0`은 버그 유발.
3. **날짜 형식은 점(.) 구분** — `Date "2024.04.08 18:00:00"` (O) / `Date "2024-04-08"` (X)
4. **SaveVars/RestoreVars** — 스크립트 시작/끝에 항상 사용하여 설정 보호.
5. **스크린샷 완료 대기** — `Screenshot { ... }` 후 `WaitTrigger "ScreenshotComplete"` 필수.
6. **이름에 공백이 있으면 따옴표** — `Select "Alpha Centauri"`. 모호성 해소: `Select "Saturn|Pandora"`.

---

## 3. 카메라 제어 명령어

### Select — 천체 선택
```
Select Earth
Select "Alpha Centauri"
Select "Saturn|Pandora"       // 부모|자식으로 모호성 해소
Select "Waypoint 1"           // 웨이포인트
Select "Path 1"               // 스플라인 경로
```

### Goto — 선택 천체로 이동
```
Goto                                     // 기본값(Time 2, DistRad 2)
Goto { Time 5 DistRad 3 }               // 5초, 반경 3배 거리
Goto { Time 0 }                          // 즉시 텔레포트
Goto { Time 10 DistKm 500 }             // 500km 거리
Goto { Time 8 Lon 86.4 Lat 13.5 HeightKm 150 }  // 좌표 위 150km
Goto { Time 5 Yaw 0 Pitch -90 Roll 0 }  // 정면 바라보기
Goto { Time 15 AccelTime 3 DecelTime 5 DriftTime 7 }  // 가감속 제어
```

**Goto 전체 파라미터:**
- `Time` — 비행 시간(초), 기본 2
- `AccelTime` / `DecelTime` / `DriftTime` — 가속/감속/등속 시간
- `AccelPower` / `DecelPower` — 가감속 곡률
- `Dist`(pc) / `DistKm`(km) / `DistRad`(반경배수, 기본2) / `HeightKm`(표면고도)
- `Lon` / `Lat` — 경도/위도(도)
- `Yaw` / `Pitch` / `Roll` — 오일러 각(도)
- `Up` — 상향 벡터
- `Center false` — 목표 방향 회전 비활성화

### Center — 카메라 회전만 (이동 없음)
```
Center { Time 5 }
```

### Horizon — 지평선 방향으로 회전
```
Horizon { Time 3 }
```

### GotoLocation — 위치 코드로 즉시 텔레포트
```
GotoLocation "Volcano under rings"
GotoLocation "Name" { Body "Earth" Parent "Earth-Moon" Date "..." Pos (...) Rot (...) }
```

### 카메라 바인딩 모드
```
Follow      // 천체 중심 추적(회전 무시)
SyncRot     // 표면 고정(회전 포함)
Free        // 바인딩 해제
Track       // 선택 천체를 화면 중앙 유지
Untrack     // 트래킹 해제
```

### FOV / MoveMode / Speed
```
FOV 90
FOV 45
MoveMode 1   // Free (관성 없음)
MoveMode 2   // Spacecraft (관성 있음, 방향 독립)
MoveMode 3   // Aircraft (관성 있음, 방향 따름)
Speed 2.5    // pc/s
SpeedKm 500  // km/s
```

### Orbit — 선택 천체 주위 공전
```
Orbit { AngularSpeed 10 Axis (0, 1, 0) FadeTime 2 Func "Cubic" }
StopOrbit { FadeTime 2 }
```
Axis 기본값: (0, 1, 0) = 극축. Func: "Linear", "Quadric", "Cubic", "Sin"

### Fly — 카메라 방향 이동
```
Fly { SpeedKm 500 FadeTime 2 Func "Cubic" }
Fly { Axis (0, 0.707, 0.707) SpeedKm 100 }
StopFly { FadeTime 1.5 }
```

### Turn — 카메라 자체 회전
```
Turn { AngularSpeed 15 Axis (0, 1, 0) FadeTime 2 }
StopTurn { FadeTime 1.5 }
```

---

## 4. 스플라인 카메라 경로

### SplinePath 정의
```
SplinePath "MyPath"
{
    Body       "Earth"
    Parent     "Sol"
    SyncRot    true           // true=표면고정, false=Follow
    Duration   30.0           // 재생 시간(초)
    PosSpline  "Catmull-Rom"  // 위치 보간
    RotSpline  "B-spline"     // 회전 보간
    SplineData
    {
        // (time, pos.x, pos.y, pos.z, rot.w, rot.x, rot.y, rot.z)
        (0.000, 1.2e-7, 5.6e-8, 3.4e-7, 0.707, 0.0, 0.707, 0.0)
        (0.500, 2.3e-7, 6.7e-8, 4.5e-7, 0.500, 0.5, 0.500, 0.5)
        (1.000, 3.4e-7, 7.8e-8, 5.6e-7, 0.707, 0.0, 0.707, 0.0)
    }
}
```

### PlaySplinePath 재생
```
Select "MyPath"
Goto "MyPath"                      // 시작점으로 부드럽게 이동
Wait 3
PlaySplinePath "MyPath"            // 재생 시작
Wait 30                             // Duration과 동일!
PlaySplinePath "MyPath" { Time 60 } // Duration 오버라이드
```

### 카메라 경로 편집기
- Main menu → Editor → Camera path editor
- 녹화 → .ssp 파일 저장 (SplinePath 명령이 담긴 스크립트)
- 스크립트에서: `Run "path.ssp"` 로 로드 후 `PlaySplinePath` 호출
- 0.991부터 저장 경로: `%USERPROFILE%\Documents\Cosmographic\SpaceEngine\addons\scripts`

---

## 5. 시간 제어

```
Date "2024.04.08 18:00:00"   // 점(.) 구분! 밀리초 가능
Date "2024.04.08"            // 00:00:00
Date "2024"                  // 01.01 00:00:00
Date "current"               // 시스템 시계

TimeScale 100                // 100배속
TimeScale 1                  // 실시간
TimeScale -100               // 역방향 100배속
// TimeScale 0 사용 금지!

StopTime                     // 시간 일시정지
StartTime                    // 시간 재개
```

---

## 6. 변수 제어

```
Set LandLOD 1.0              // 범위 체크 O
SetForce BloomBright 0.7     // 모든 모드에 적용
Reset LandLOD                // 기본값 복원

Interpolate BloomBright { From 0 To 1 Time 3 Func "quadric" }
// Func: "linear", "quadric", "cubic", "sin", "exp", "revexp"

SaveVars                     // 현재 변수 상태 저장
RestoreVars                  // 저장된 상태 복원 (스크립트 종료 시 자동)
```

---

## 7. 성능/그래픽 핵심 변수

| 변수 | 타입 | 기본 | 범위 | 용도 |
|------|------|------|------|------|
| QualityPreset | int | 4 | 0~4 | 전체 품질 (0=최저, 4=울트라) |
| LandLOD | float | 0 | -1~1 | 지형 LOD |
| LandLODmaxRes | int | 1080 | 480~6480 | 지형 최대 해상도 |
| FBOResolution | float | 0.35 | 0.1~1 | 프레임버퍼 해상도 비율 |
| MSAALevel | int | 0 | 0~32 | MSAA 레벨 |
| FXAA | bool | true | — | FXAA |
| AnisotropyLevel | int | 0 | 0~16 | 이방성 필터링 |
| BloomBright | float | 0.7 | 0~1 | 블룸 밝기 |
| MaxTilesPerFrame | int | 8 | 1~20 | 프레임당 타일 로드 |
| MaxTimePerFrame | int | 8 | 1~100 | 프레임당 처리 시간 |
| MaxThreads | int | 10 | 1~10 | 최대 스레드 |
| DrawClouds | bool | true | — | 구름 렌더링 |
| DrawWater | bool | true | — | 물 렌더링 |
| AuroraQuality | int | 1 | 0~1 | 오로라 품질 |
| BlackHoleQuality | int | 2 | 0~3 | 블랙홀 품질 |
| VSync | int | 2 | 0~2 | 수직 동기화 |

### 영상/이미지 변수

| 변수 | 타입 | 기본 | 범위 |
|------|------|------|------|
| JpegQuality | int | 85 | 0~100 |
| ExposureComp | float | 0 | -42~4 |
| Brightness | float | 1 | 0~2 |
| Contrast | float | 1 | 0~2 |
| Saturation | float | 1 | 0~2 |
| Gamma | float | 1 | 0~2 |
| Sharpness | float | 0 | 0~2 |
| MotionBlurLength | float | 0 | -10~10 |

---

## 8. 렌더링/표시 제어

### Show / Hide — 오버레이
```
Show Orbits
Hide Clouds
Show Constellations
```
가능한 값: Planets, Stars, Clusters, Nebulae, Galaxies, Atmo, Atmospheres,
Clouds, Water, Aurora, CometTails, AccretionDisks, Jets, Orbits, OrbitMarks,
EclipseMask, Vectors, SelPointer, VelVector, Grids, Constellations,
Labels, Markers, NightLights, Eclipses, PlanetShine, LensFlares, PseudoFlares

### FadeOut / FadeIn
```
FadeOut { Time 2 Color (0, 0, 0) }
FadeIn { Time 2 }
```

### ShowObject / HideObject
```
HideObject "Mars"
ShowObject "Jupiter|Io" { Time 3 }
```

---

## 9. 스크린샷

```
Screenshot
Screenshot { GUI false Format "png" Name "myshot" Path "screenshots/tour/" }
WaitTrigger "ScreenshotComplete"   // 저장 완료 대기 필수!
```
Format: "jpg", "tif", "tga", "png", "dds"

---

## 10. UI/메시지

```
Print "Hello" { Time 10 Color (1, 1, 1, 1) PosX 0.5 PosY 0.1 AlignX "center" }
HidePrint

ShowMessage "Non-blocking message"
WaitMessage "Blocking — waits for Next button"
HideMessage

ShowDialog "Settings" { Tab "graphics" }
ShowDialog "Find object"
HideDialog "Solar system browser"
HideAllDialogs
HideAllToolbars
```

---

## 11. 스크립트 제어

```
Run "filename"              // data/scripts/ 에서 filename.se 실행
Run "path/file.se"          // 상대 경로 (중첩 16회까지)
Break                       // 스크립트 중단
Wait 5                      // 5초 대기
CheckVersion 990            // 버전 확인
```

### 조건문 (중첩 불가!)
```
if { TimeScale > 100 }
    Set TimeScale 100
elif { TimeScale < 1 }
    Set TimeScale 1
else
    Print "Normal"
endif
```
연산자: `==`, `!=`, `<`, `>`, `<=`, `>=`

### 반복
```
Loop
    commands
EndLoop
```

---

## 12. 트리거

```
WaitTrigger "LoadingComplete"
WaitTrigger "ScreenshotComplete"
WaitTrigger "Object|Select" { Object "Earth" }
WaitTrigger "Object|Approach" { Object "Mars" RangeRad (1.5, 3.0) }
WaitTrigger "Object|See" { Object "Waypoint 1" ActivationDelay 3 AnimateObject "Fill" }
WaitTrigger "Time" { Time "2024.04.08" Mode "Later" }
WaitTrigger "Control|Goto"

BeginMultiTrigger "AND"
    WaitTrigger "Object|Select" { Object "Earth" }
    WaitTrigger "Control|Center"
EndMultiTrigger
```

주요 트리거: LoadingComplete, ScreenshotComplete, Object|Select, Object|Approach,
Object|See, Time, Control|Goto, Control|Center, Control|Rotate, Control|Move,
GUI|Open, GUI|Close, GUI|ChangeValue, EnterPlanetarium, EnterSinglePlayer

---

## 13. 웨이포인트

```
Waypoint "Marker 1"
{
    Parent         "Earth"
    Visible        true
    Label          true
    Shape          "Circle"      // Circle/Triangle/Square/Diamond/Hexagon/Billboard/Sphere
    Color          (1, 0.8, 0, 0.6)
    RadiusKm       500
    StaticPosXYZ   (1.0, 0.5, 0.7)    // Follow 모드(회전 무시)
    FixedPosPolar  (32.9, 60.3, 7500)  // SyncRot 모드(표면 고정)
    FadeRangeKm    (10, 20, 900, 1000) // 가시 거리 범위
}
DeleteWaypoint "Marker 1"
ClearWaypoints
```

---

## 14. 사용자 제어 제한

```
UserMoveControl "disabled"     // 이동 금지
UserMoveControl "free"         // 이동 허용
UserMoveControl "limited" { Center "Mars" DistRad 5 SpeedKm 500 }

UserRotationControl "disabled" / "free"
UserTimeControl "disabled" / "free"
UserTimeControl "limited" { TimeRange ("2024.01.01", "2024.12.31") TimeRateRange (1, 100) }
```

---

## 15. 사운드

```
PlayMusic "ambient_space.ogg"
PauseMusic
ResumeMusic
```

---

## 16. 파일시스템 구조

```
SpaceEngine/
├── data/                           ← 기본 데이터 (수정 금지)
│   ├── catalogs/stars/*.sc
│   ├── catalogs/planets/*.sc
│   ├── catalogs/galaxies/*.sc
│   ├── scripts/*.se
│   └── Catalogs0980.pak            ← zip 아카이브
├── addons/                         ← 사용자 애드온 (높은 우선순위)
│   ├── catalogs/stars/*.sc
│   ├── catalogs/planets/*.sc
│   └── scripts/*.se
├── config/
│   ├── main-user.cfg               ← 모든 설정 (삭제시 기본값 재생성)
│   ├── save-user.cfg               ← 카메라 위치/시간
│   ├── places-user.cfg             ← 저장된 위치
│   └── spacecraft.cfg              ← 우주선
├── system/
│   ├── SpaceEngine.exe
│   └── se.log                      ← 로그 파일
└── screenshots/

0.991부터 추가 경로:
%USERPROFILE%\Documents\Cosmographic\SpaceEngine\
├── addons/                         ← 3번째 검색 경로
├── screenshots/
├── videos/
├── logs/
└── exports/
```

### .pak 파일 규칙
- .pak = .zip 확장자 변경. Deflate 압축만 지원.
- addons 폴더가 data 폴더보다 높은 우선순위.
- 같은 가상 경로의 파일이 여러 개면 수정일이 최신인 것 로드.
- .pak 최대 4GB. ogg 음악/사운드는 pak에 넣을 수 없음.

---

## 17. 카탈로그(.sc) 형식

### 항성 생성
```
Star "MyStarName"
{
    RA        16 10 45        // 적경 (시 분 초)
    Dec      -25 12 11        // 적위 (도 분 초)
    Dist      100.0           // 거리(pc)
    Class    "G2V"            // 분광형
    MassSol   1.0             // 태양 질량 단위
    RadSol    1.0             // 태양 반경 단위
    Teff      5778            // 표면 온도(K)
    Lum       1.0             // 광도(태양 단위)
}
```
항성 Class: O/B/A/F/G/K/M + 광도 V/III/I 등. 특수: X=블랙홀, Q=중성자별, Z=웜홀, P=떠돌이행성
쌍성: StarBarycenter로 항성카탈로그에 등록 → 행성카탈로그에서 개별 Star로 궤도 기술

### 행성 생성 (최소)
```
Planet "MyPlanet"
{
    ParentBody  "MyStarName"
    Radius      7200           // km (또는 Mass 1.5)
    Orbit
    {
        SemiMajorAxis  1.0     // AU (또는 Period 1.0 년)
    }
}
```

### 행성 생성 (상세)
```
Planet "MyEarth"
{
    ParentBody    "MyStarName"
    Class         "Terra"          // Terra/GasGiant/IceGiant/Desert/Ocean 등
    Mass          1.0
    Radius        6371
    Obliquity     23.4
    RotationPeriod 24

    Life { Class "Organic" Type "Multicellular" Biome "Terrestrial" }

    Surface
    {
        seaLevel      0.5
        snowLevel     0.85
        BumpHeight    15
        colorSea      (0.04, 0.2, 0.2, 1)
        colorDesert   (0.42, 0.36, 0.22, 0)
        colorLowPlants (0.12, 0.15, 0.08, 0)
    }

    Atmosphere
    {
        Model      "Earth"        // "Earth", "Thick", "Thin" 등
        Height     100
        Pressure   1.0
        Greenhouse 33
        Composition { N2 78 O2 21 Ar 0.93 CO2 0.04 }
    }

    Ocean { Height 5 }
    Clouds { Coverage 0.5 Height 5 }
    Aurora { Height 200 NorthLat 65 NorthRadius 3000 }
    Rings { InnerRadius 10000 OuterRadius 50000 }

    NoRings     true              // Rings 태그 무시
    NoLife      true              // Life 태그 무시
    NoClouds    true              // Clouds 태그 무시

    Orbit
    {
        RefPlane        "Ecliptic"
        SemiMajorAxis   1.0       // AU
        Period          1.0       // 년
        Eccentricity    0.017
        Inclination     0.0
        AscendingNode   0.0
        ArgOfPericenter 0.0
        MeanAnomaly     0.0
    }
}
```

### 객체 삭제
```
Remove "ObjectName"                          // 항성
Remove "PlanetName" { ParentBody "StarName" } // 행성
```

---

## 18. 비디오 캡처

- **F9** — 비디오 캡처 메뉴
- **Ctrl+F9** — 녹화 시작/정지
- 코덱: H.264(기본, 대부분 GPU), HEVC(H.265, 고품질), AV1(최신 GPU), SVT/AOM Software AV1(CPU)
- 오프라인 렌더링: 고정 FPS 모드 — SE가 프레임 속도를 보장
- 스트리밍 모드: 실시간 캡처

---

## 19. MCP 서버 고급 도구 설계

구현 예정인 고급 MCP 도구 8종:

| 도구 | 기능 |
|------|------|
| `camera_orbit` | 천체 주위 공전 (축/속도/시간 제어) |
| `camera_flyby` | 접근 플라이바이 + 도착 후 공전 옵션 |
| `play_recorded_path` | 녹화된 .ssp 카메라 경로 재생 |
| `screenshot_sequence` | 공전하며 연속 스크린샷 촬영 |
| `set_performance` | 5단계 프리셋 (ultra/high/balanced/low/potato) |
| `cinematic_shot` | 시네마틱 숏 (orbit/approach/sunrise/flyover/pull_back) |
| `educational_tour` | 교육 투어 (페이드/타임랩스/스크린샷/메시지) |
| `restore_defaults` | 모든 변경 설정 복원 |

---

## 20. 커뮤니티 도구

| 도구 | 링크 | 기능 |
|------|------|------|
| Space-Engine-Toolkit | github.com/JohnKServices/Space-Engine-Toolkit | C++ 외부→콘솔 브릿지 (testVar, command) |
| se-lang | github.com/Aluriak/se-lang | Python으로 .sc 카탈로그 프로그래밍 생성 |
| spaceengine | github.com/Aluriak/spaceengine | Python SE 애드온 콘텐츠 인터페이스 |
| speng-hunter | github.com/Centri3/speng-hunter | 매크로 기반 희귀 천체 자동 탐색 |
