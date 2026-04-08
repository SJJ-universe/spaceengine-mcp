"""
SpaceEngine MCP — Pydantic 데이터 모델

Phase 1~4 기존 모델 + Phase 5 신규 모델
"""

from typing import Literal

from pydantic import BaseModel, Field


# ── Phase 1~2 모델 ──────────────────────────────────────────────────────────

class OrbitParams(BaseModel):
    semi_major_axis: float = Field(1.0, description="궤도 장반경 (AU)", gt=0)
    period: float | None = Field(None, description="궤도 주기 (년)")
    eccentricity: float = Field(0.0, description="이심률 (0~1)", ge=0, lt=1)
    inclination: float = Field(0.0, description="궤도 경사각 (도)", ge=0, le=180)


class StarParams(BaseModel):
    name: str = Field(description="항성 이름")
    spectral_class: str = Field("G2 V", description="분광형 (예: G2 V, K5 V)")
    mass: float = Field(1.0, description="태양 질량 단위")
    radius: float = Field(1.0, description="태양 반경 단위")
    temperature: int = Field(5778, description="표면 온도 (K)")
    luminosity: float = Field(1.0, description="태양 광도 단위")


class PlanetParams(BaseModel):
    name: str = Field(description="행성 이름")
    parent: str = Field(description="부모 천체 이름")
    planet_class: Literal["Terra", "GasGiant", "IceGiant", "Desert", "Ocean", "Titan"] = "Terra"
    mass: float = Field(1.0, description="지구 질량 단위")
    radius: float = Field(6371, description="반경 (km)")
    orbit: OrbitParams = Field(default_factory=OrbitParams)
    has_atmosphere: bool = True
    has_water: bool = False


class TourStop(BaseModel):
    target: str = Field(description="천체 이름")
    wait_seconds: int = Field(10, description="머무는 시간 (초)")
    distance_rad: float = Field(3.0, description="관측 거리 (천체 반경 배수)")
    message: str | None = Field(None, description="화면에 표시할 텍스트")


# ── Phase 5 모델 ─────────────────────────────────────────────────────────────

class SplineKnot(BaseModel):
    """스플라인 경로의 단일 노트(키프레임)"""
    select: str | None = Field(None, description="이 노트에서 선택할 천체 이름")
    goto_params: str | None = Field(None, description="Goto 파라미터 (예: 'DistRad 5 Time 3')")
    fov: float | None = Field(None, description="이 노트에서의 시야각 (도)")
    wait: float | None = Field(None, description="이 노트에서 대기 시간 (초)")


# ── Phase 6 모델 ─────────────────────────────────────────────────────────────

class MoonParams(BaseModel):
    """위성 생성 파라미터"""
    name: str = Field(description="위성 이름")
    parent: str = Field(description="부모 행성 이름")
    moon_class: Literal["Selena", "Terra", "IceWorld", "Desert", "Titan"] = "Selena"
    mass: float = Field(0.01, description="지구 질량 단위")
    radius: float = Field(1737, description="반경 (km)")
    orbit: OrbitParams = Field(default_factory=OrbitParams)
    tidal_locked: bool = False


class BarycenterParams(BaseModel):
    """쌍성계 무게중심 파라미터"""
    name: str = Field(description="무게중심 이름")
    mass: float = Field(1.0, description="전체 질량 (태양 질량 단위)")


class RingSystemParams(BaseModel):
    """행성 고리 파라미터"""
    inner_radius: float = Field(description="내부 반경 (km)")
    outer_radius: float = Field(description="외부 반경 (km)")
    texture: str | None = Field(None, description="텍스처 파일명")
    composition: str | None = Field(None, description="구성 물질 (Ice, Rock, Dust 등)")


class AtmosphereParams(BaseModel):
    """대기 상세 파라미터"""
    pressure: float = Field(1.0, description="표면 기압 (atm)")
    height: float | None = Field(None, description="대기 높이 (km)")
    composition: dict[str, float] | None = Field(None, description="가스 조성 (예: {'N2': 0.78, 'O2': 0.21})")
    greenhouse: float | None = Field(None, description="온실 효과 계수")


class SurfaceParams(BaseModel):
    """지형 상세 파라미터"""
    style: float | None = Field(None, description="지형 스타일 번호")
    color_map: str | None = Field(None, description="컬러맵 파일명")
    height_scale: float | None = Field(None, description="지형 높이 스케일")
    snow_level: float | None = Field(None, description="적설 고도")


class NebulaParams(BaseModel):
    """성운 생성 파라미터"""
    name: str = Field(description="성운 이름")
    nebula_type: Literal["Emission", "Reflection", "Dark", "Planetary"] = "Emission"
    radius: float = Field(description="반경 (광년)")
    brightness: float = Field(1.0, description="밝기")
    ra: float | None = Field(None, description="적경 (시)")
    dec: float | None = Field(None, description="적위 (도)")


class GalaxyParams(BaseModel):
    """은하 생성 파라미터"""
    name: str = Field(description="은하 이름")
    galaxy_type: Literal["Spiral", "Elliptical", "Irregular", "Lenticular"] = "Spiral"
    radius: float = Field(description="반경 (kpc)")
    mass: float = Field(description="질량 (10^10 태양질량 단위)")
    ra: float | None = Field(None, description="적경 (시)")
    dec: float | None = Field(None, description="적위 (도)")
