import hashlib
import unicodedata
from datetime import date, datetime
from typing import Any

from src.utils.time import ensure_utc


CULTURE_PROFILES: dict[str, dict[str, Any]] = {
    "soja": {
        "ideal_precip_7d_mm": 28.0,
        "heat_threshold_c": 33.5,
        "zarc_windows": [("09-15", "12-31")],
    },
    "milho": {
        "ideal_precip_7d_mm": 24.0,
        "heat_threshold_c": 34.5,
        "zarc_windows": [("01-05", "03-20"), ("09-01", "11-30")],
    },
    "algodao": {
        "ideal_precip_7d_mm": 20.0,
        "heat_threshold_c": 35.5,
        "zarc_windows": [("11-01", "01-31")],
    },
}

DEFAULT_CULTURE_PROFILE = {
    "ideal_precip_7d_mm": 25.0,
    "heat_threshold_c": 34.0,
    "zarc_windows": [("09-15", "12-31")],
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _hash_ratio(seed_text: str) -> float:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _in_zarc_window(sowing_date: date, windows: list[tuple[str, str]]) -> bool:
    mmdd = sowing_date.strftime("%m-%d")
    for start, end in windows:
        if start <= end and start <= mmdd <= end:
            return True
        if start > end and (mmdd >= start or mmdd <= end):
            return True
    return False


def _infer_crop_stage(sowing_date: date, analysis_timestamp: datetime) -> str:
    analysis_date = ensure_utc(analysis_timestamp).date()
    delta_days = (analysis_date - sowing_date).days
    if delta_days < 0:
        return "pre-plantio"
    if delta_days <= 20:
        return "emergencia"
    if delta_days <= 50:
        return "vegetativo"
    if delta_days <= 90:
        return "florescimento"
    if delta_days <= 130:
        return "enchimento_de_graos"
    return "maturacao"


def get_agro_context(inputs: dict[str, Any], spatial_context: dict[str, Any]) -> dict[str, Any]:
    culture_raw = inputs["culture"]
    culture = _normalize_text(culture_raw)
    profile = CULTURE_PROFILES.get(culture, DEFAULT_CULTURE_PROFILE)

    sowing_date: date = inputs["sowing_date"]
    analysis_timestamp: datetime = inputs["analysis_timestamp"]
    irrigated: bool = bool(inputs.get("irrigated", False))
    municipio = spatial_context["municipio"]

    crop_stage = inputs.get("crop_stage") or _infer_crop_stage(sowing_date, analysis_timestamp)
    zarc_flag = _in_zarc_window(sowing_date, profile["zarc_windows"])

    volatility_seed = f"{municipio}:{culture}:volatility"
    trend_seed = f"{municipio}:{culture}:trend"
    territorial_seed = f"{spatial_context['centroid_lat']}:{spatial_context['centroid_lon']}"

    yield_volatility = round(0.08 + _hash_ratio(volatility_seed) * 0.18, 3)
    yield_mean_index = round(0.85 + _hash_ratio(trend_seed) * 0.35, 3)
    trend_value = _hash_ratio(f"{trend_seed}:direction")
    if trend_value < 0.33:
        yield_trend = "queda"
    elif trend_value < 0.66:
        yield_trend = "estavel"
    else:
        yield_trend = "alta"

    vegetation_stress_index = round(0.35 + _hash_ratio(territorial_seed) * 0.5, 3)
    soil_water_buffer_index = round(0.25 + _hash_ratio(territorial_seed + ":soil") * 0.6, 3)
    vulnerability_index = round(
        (vegetation_stress_index * 0.55) + ((1.0 - soil_water_buffer_index) * 0.45),
        3,
    )

    return {
        "culture": culture,
        "culture_label": culture_raw.strip().lower(),
        "sowing_date": sowing_date.isoformat(),
        "crop_stage": crop_stage,
        "irrigated": irrigated,
        "zarc_flag": zarc_flag,
        "culture_profile": profile,
        "historical_yield_context": {
            "yield_mean_index": yield_mean_index,
            "yield_volatility": yield_volatility,
            "yield_trend": yield_trend,
        },
        "territorial_context": {
            "alphaearth_cluster": f"mt_cluster_{int(_hash_ratio(territorial_seed + ':cluster') * 5) + 1}",
            "vegetation_stress_index": vegetation_stress_index,
            "soil_water_buffer_index": soil_water_buffer_index,
            "vulnerability_index": vulnerability_index,
        },
    }

