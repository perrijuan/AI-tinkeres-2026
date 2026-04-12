from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Geometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class AnalysisRequest(BaseModel):
    field_id: str | None = None
    property_name: str | None = None
    culture: str = Field(..., min_length=2, max_length=50)
    sowing_date: date
    crop_stage: str | None = None
    irrigated: bool = False
    analysis_timestamp: datetime
    geometry: Geometry


class ForecastPoint(BaseModel):
    forecast_time: str
    precip_mm: float
    temp_c: float
    humidity_pct: float


class FieldInfo(BaseModel):
    field_id: str | None = None
    property_name: str | None = None
    culture: str
    municipio: str
    uf: str
    area_ha: float
    irrigated: bool


class Summary(BaseModel):
    risk_score: int
    risk_level: str
    primary_alert: str
    recommended_action: str
    analysis_timestamp: str
    forecast_run_timestamp: str


class Metrics(BaseModel):
    precip_forecast_7d_mm: float
    precip_forecast_14d_mm: float
    temp_mean_7d_c: float
    temp_max_7d_c: float
    humidity_mean_7d_pct: float


class RiskFlags(BaseModel):
    dry_risk_flag: bool
    heat_risk_flag: bool
    outside_zarc_flag: bool
    vegetation_stress_flag: bool


class MapLayer(BaseModel):
    geometry: dict[str, Any]
    fill_color: str
    stroke_color: str
    tooltip_summary: str


class CopilotResponse(BaseModel):
    summary: str
    why: list[str]
    action: str


class AnalysisResponse(BaseModel):
    field_info: FieldInfo
    summary: Summary
    metrics: Metrics
    risk_flags: RiskFlags
    forecast_timeseries: list[ForecastPoint]
    map_layer: MapLayer
    copilot_response: CopilotResponse
