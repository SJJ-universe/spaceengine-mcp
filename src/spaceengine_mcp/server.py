"""
SpaceEngine MCP Server — FastMCP 기반 메인 서버 정의

Phase별 도구 모듈은 tools/ 하위에 정의되어 있으며
이 파일에서 register_tools()를 호출하여 등록합니다.

Resources / Prompts는 이 파일에 직접 정의합니다.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from spaceengine_mcp.bridges.catalog_bridge import CatalogBridge
from spaceengine_mcp.bridges.script_bridge import ScriptBridge, normalize_overlay_name
from spaceengine_mcp.bridges.config_bridge import ConfigBridge
from spaceengine_mcp.bridges.state_bridge import StateBridge
from spaceengine_mcp.config import SpaceEngineConfig

# ── 서버 초기화 ─────────────────────────────────────────────────────────────
mcp = FastMCP("spaceengine")
config = SpaceEngineConfig()
script_bridge = ScriptBridge(config, templates_dir=str(Path(__file__).parent.parent.parent / "templates"))
catalog_bridge = CatalogBridge(config)
config_bridge = ConfigBridge(config)
state_bridge = StateBridge(config)


# ── Tool 등록 (Phase별 모듈) ──────────────────────────────────────────────────
from spaceengine_mcp.tools import (  # noqa: E402
    phase1_navigation,
    phase2_creation,
    phase3_camera,
    phase4_advanced,
    phase5_console,
    phase6_catalog,
    phase7_keyboard,
    phase8_filesystem,
    phase9_intelligence,
    phase10_flight,
    phase11_workflow,
)

phase1_navigation.register_tools(mcp, script_bridge, catalog_bridge)
phase2_creation.register_tools(mcp, script_bridge, catalog_bridge)
phase3_camera.register_tools(mcp, script_bridge, config)
phase4_advanced.register_tools(mcp, script_bridge, catalog_bridge)
phase5_console.register_tools(mcp, script_bridge)
phase6_catalog.register_tools(mcp, script_bridge, catalog_bridge)
phase7_keyboard.register_tools(mcp)
phase8_filesystem.register_tools(mcp, config_bridge, catalog_bridge, script_bridge, config)
phase9_intelligence.register_tools(mcp, state_bridge, script_bridge)
phase10_flight.register_tools(mcp, script_bridge, state_bridge)
phase11_workflow.register_tools(mcp, script_bridge, state_bridge, config)


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("spaceengine://catalogs/stars")
def resource_star_catalogs() -> str:
    """커스텀 항성 카탈로그 목록"""
    items = catalog_bridge.list_addon_catalogs("stars")
    if not items:
        return "생성된 항성 카탈로그 없음"
    return "\n".join(f"- {i['name']} ({i['path']})" for i in items)


@mcp.resource("spaceengine://catalogs/planets")
def resource_planet_catalogs() -> str:
    """커스텀 행성 카탈로그 목록"""
    items = catalog_bridge.list_addon_catalogs("planets")
    if not items:
        return "생성된 행성 카탈로그 없음"
    return "\n".join(f"- {i['name']} ({i['path']})" for i in items)


@mcp.resource("spaceengine://config")
def resource_config() -> str:
    """현재 SpaceEngine 설정 정보"""
    warnings = config.validate()
    lines = [
        f"설치 경로: {config.install_path}",
        f"실행 파일: {config.executable}",
        f"스크립트 디렉토리: {config.scripts_dir}",
        f"로그 파일: {config.log_file}",
    ]
    if warnings:
        lines.append("\n[경고]")
        lines.extend(f"  - {w}" for w in warnings)
    return "\n".join(lines)


@mcp.resource("spaceengine://scripts/recent")
def resource_recent_scripts() -> str:
    """최근 생성된 MCP 스크립트 목록"""
    scripts_dir = config.scripts_dir
    if not scripts_dir.exists():
        return "스크립트 없음"
    scripts = sorted(scripts_dir.glob("mcp_*.se"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
    if not scripts:
        return "최근 스크립트 없음"
    return "\n".join(f"- {p.name}" for p in scripts)


# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt()
def explore_space() -> str:
    """SpaceEngine 우주 탐험 가이드 — 사용 가능한 도구와 활용법 안내"""
    return """당신은 SpaceEngine 우주 엔진을 제어하는 AI 비서입니다.
사용자의 자연어 요청을 SpaceEngine MCP 도구 호출로 변환합니다.

## 사용 가능한 도구 카테고리

### 탐색 (Navigation)
- **navigate_to**: 천체로 이동 (예: "화성으로 가줘", "시리우스 보여줘")
- **follow_object**: 천체 추적 (follow=카메라 따라감, track=시선 고정)

### 카메라 (Camera)
- **control_camera**: 줌인/줌아웃, 시야각 변경 (dist, dist_rad, fov)
- **take_screenshot**: 현재 화면 캡처
- **create_flyby**: 천체 근접비행 시나리오
- **camera_flight**: Fly/Turn/Orbit 자유 카메라 비행
- **set_speed**: 카메라 이동 속도 설정

### 시간 (Time)
- **set_time**: 특정 날짜/시각 설정 또는 시간 가속/정지

### 천체 생성 (Creation)
- **create_star**: 커스텀 항성 생성
- **create_planet**: 커스텀 행성 생성
- **create_tour**: 복수 천체 순서 방문 투어

### 변수 / 애니메이션 (Variables)
- **set_variable**: SE 내부 변수 설정/초기화
- **interpolate_variable**: 변수 부드러운 애니메이션

### 경로 / 웨이포인트 (Paths)
- **create_spline_path**: 스플라인 카메라 경로 정의+재생
- **manage_waypoints**: 웨이포인트 생성/삭제/이동

### 표시 (Display)
- **toggle_overlay**: 궤도선, 라벨, 별자리 등 표시/숨김
- **set_rendering**: 렌더링 설정 (대기, 구름 등)
- **show_message / hide_message**: 화면 텍스트 표시
- **advanced_message**: BBCode 서식 메시지 / WaitMessage
- **toggle_gui**: UI 패널 표시/숨김
- **manage_dialogs**: 다이얼로그 열기/닫기
- **fade_effect**: 화면 페이드 전환 효과

### 사운드 (Sound)
- **play_sound / stop_sound**: 효과음 재생

### 상태 (State)
- **save_state / restore_state**: 카메라 위치/시간 저장 & 복원

### 시스템 (System)
- **read_log**: SE 로그 분석
- **run_script**: 커스텀 .se 스크립트 직접 실행

## 예시 요청 → 도구 매핑
- "화성에 가서 스크린샷 찍어줘" → navigate_to → take_screenshot
- "시네마틱 카메라 경로 만들어줘" → create_spline_path
- "밝기를 서서히 줄여줘" → interpolate_variable(variable="StarBrightness", ...)
- "화면 페이드 아웃" → fade_effect(action="fade_out")
"""


@mcp.prompt()
def design_solar_system() -> str:
    """커스텀 항성계 설계 가이드"""
    return """커스텀 항성계를 설계하세요!

## 단계
1. **항성 생성**: create_star로 중심 별 만들기
   - 분광 유형: O/B/A/F/G/K/M
   - 온도, 반지름, 광도 설정

2. **행성 추가**: create_planet로 행성 배치
   - 궤도 파라미터: 장반경(SemiMajorAxis), 이심률(Eccentricity)
   - 행성 유형: Terra, GasGiant, IceGiant

3. **투어 생성**: create_tour로 항성계 투어
   - 항성 → 내행성 → 외행성 순서
"""


@mcp.prompt()
def cinematic_guide() -> str:
    """시네마틱 영상 촬영 가이드"""
    return """SpaceEngine에서 시네마틱 장면을 연출하세요!

## 촬영 워크플로
1. **위치 설정**: navigate_to로 목표 천체 이동
2. **카메라 조정**: control_camera로 거리/FOV 세밀 조정
3. **UI 정리**: toggle_gui(false)로 메뉴 숨김
4. **오버레이 정리**: toggle_overlay로 궤도선/라벨 숨김
5. **상태 저장**: save_state로 현재 구도 저장
6. **스크린샷**: take_screenshot으로 캡처

## 고급 기법
- **스플라인 경로**: create_spline_path로 부드러운 카메라 이동 경로
- **변수 애니메이션**: interpolate_variable로 밝기/효과 부드럽게 전환
- **페이드**: fade_effect로 장면 전환
- **플라이바이**: create_flyby로 접근 장면 만들기
- **FOV 변경**: fov=10 (망원렌즈) / fov=90 (광각)
- **시간대 선택**: set_time으로 일출/일몰 시간 설정
"""
