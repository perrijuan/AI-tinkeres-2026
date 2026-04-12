import hashlib
import unicodedata
from datetime import date, datetime
from typing import Any

from src.features.soil_context import get_soil_context
from src.features.zarc_lookup import get_zarc_context
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


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


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


def _build_fallback_territorial_context(spatial_context: dict[str, Any]) -> dict[str, Any]:
    territorial_seed = f"{spatial_context['centroid_lat']}:{spatial_context['centroid_lon']}"
    vegetation_stress_index = round(0.35 + _hash_ratio(territorial_seed) * 0.5, 3)
    soil_water_buffer_index = round(0.25 + _hash_ratio(territorial_seed + ":soil") * 0.6, 3)
    vulnerability_index = round(
        (vegetation_stress_index * 0.55) + ((1.0 - soil_water_buffer_index) * 0.45),
        3,
    )
    return {
        "source": "heuristic",
        "provider": "SafraViva Heuristic Territory",
        "alphaearth_cluster": f"mt_cluster_{int(_hash_ratio(territorial_seed + ':cluster') * 5) + 1}",
        "vegetation_stress_index": vegetation_stress_index,
        "soil_water_buffer_index": soil_water_buffer_index,
        "vulnerability_index": vulnerability_index,
        "signals": [
            f"Indice de estresse vegetativo: {vegetation_stress_index} (fallback heuristico).",
            f"Indice de buffer hidrico do solo: {soil_water_buffer_index} (fallback heuristico).",
        ],
        "ndvi": None,
        "evi": None,
        "lst_c": None,
        "cloud_cover_pct": None,
        "last_image": None,
        "ndvi_timeseries": [],
    }


def _summarize_ndvi_dynamics(territorial_context: dict[str, Any]) -> dict[str, Any]:
    timeseries = list(territorial_context.get("ndvi_timeseries", []))
    timeseries = [point for point in timeseries if point.get("ndvi") is not None]
    latest_ndvi = territorial_context.get("ndvi")
    if latest_ndvi is None and timeseries:
        latest_ndvi = timeseries[-1].get("ndvi")

    ndvi_delta_30d = 0.0
    ndvi_anomaly = 0.0
    ndvi_trend = "stable"

    if latest_ndvi is not None and len(timeseries) >= 2:
        ref_ndvi = float(timeseries[0]["ndvi"])
        ndvi_delta_30d = round(float(latest_ndvi) - ref_ndvi, 3)
        baseline_values = [float(point["ndvi"]) for point in timeseries[:-1]]
        baseline = sum(baseline_values) / max(1, len(baseline_values))
        ndvi_anomaly = round(float(latest_ndvi) - baseline, 3)
    elif latest_ndvi is not None:
        ndvi_anomaly = round(float(latest_ndvi) - 0.55, 3)

    if ndvi_delta_30d <= -0.05:
        ndvi_trend = "decreasing"
    elif ndvi_delta_30d >= 0.05:
        ndvi_trend = "increasing"

    ndvi_drop_flag = ndvi_delta_30d <= -0.05 or ndvi_anomaly <= -0.06
    return {
        "ndvi_delta_30d": ndvi_delta_30d,
        "ndvi_anomaly": ndvi_anomaly,
        "ndvi_trend": ndvi_trend,
        "ndvi_drop_flag": ndvi_drop_flag,
    }


def _merge_soil_with_territory(
    territorial_context: dict[str, Any],
    soil_context: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(territorial_context)
    merged["soil_context"] = soil_context
    merged["soil_quality_index"] = soil_context["soil_quality_index"]
    merged["soil_quality_label"] = soil_context["soil_quality_label"]
    merged["soil_good_flag"] = soil_context["soil_good_flag"]
    merged["soil_sample_count"] = soil_context["sample_count"]
    merged["soil_nearest_sample_km"] = soil_context["nearest_sample_km"]

    ndvi_dynamics = _summarize_ndvi_dynamics(merged)
    merged.update(ndvi_dynamics)
    merged["vegetation_mismatch_flag"] = bool(ndvi_dynamics["ndvi_drop_flag"] and soil_context["soil_good_flag"])
    merged["stress_mismatch_index"] = round(
        _clamp(
            max(0.0, -ndvi_dynamics["ndvi_delta_30d"]) * (0.5 + (soil_context["soil_quality_index"] * 0.5)),
            0.0,
            1.0,
        ),
        3,
    )

    current_soil_buffer = float(merged.get("soil_water_buffer_index", 0.5))
    blended_soil_buffer = round(_clamp((current_soil_buffer * 0.6) + (soil_context["soil_quality_index"] * 0.4), 0.0, 1.0), 3)
    merged["soil_water_buffer_index"] = blended_soil_buffer

    vegetation_stress = float(merged.get("vegetation_stress_index", 0.5))
    vulnerability = round(
        _clamp((vegetation_stress * 0.55) + ((1.0 - blended_soil_buffer) * 0.45), 0.0, 1.0),
        3,
    )
    if merged["vegetation_mismatch_flag"]:
        vulnerability = round(_clamp(vulnerability + 0.08, 0.0, 1.0), 3)
    merged["vulnerability_index"] = vulnerability

    signals = list(merged.get("signals", []))
    signals.extend(soil_context.get("signals", []))
    signals.append(f"Tendencia NDVI recente: {ndvi_dynamics['ndvi_trend']}.")
    signals.append(f"Delta NDVI (janela recente): {ndvi_dynamics['ndvi_delta_30d']}.")
    if merged["vegetation_mismatch_flag"]:
        signals.append("Mismatch NDVI-solo detectado: vegetacao em queda com solo potencialmente favoravel.")
    merged["signals"] = signals
    return merged


def get_agro_context(
    inputs: dict[str, Any],
    spatial_context: dict[str, Any],
    territorial_context_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    culture_raw = inputs["culture"]
    culture = _normalize_text(culture_raw)
    profile = CULTURE_PROFILES.get(culture, DEFAULT_CULTURE_PROFILE)

    sowing_date: date = inputs["sowing_date"]
    analysis_timestamp: datetime = inputs["analysis_timestamp"]
    irrigated: bool = bool(inputs.get("irrigated", False))
    municipio = spatial_context["municipio"]

    crop_stage = inputs.get("crop_stage") or _infer_crop_stage(sowing_date, analysis_timestamp)
    heuristic_zarc_flag = _in_zarc_window(sowing_date, profile["zarc_windows"])
    zarc_context = get_zarc_context(culture_raw, municipio, sowing_date.isoformat(), heuristic_zarc_flag)
    zarc_flag = bool(zarc_context["zarc_flag"])

    volatility_seed = f"{municipio}:{culture}:volatility"
    trend_seed = f"{municipio}:{culture}:trend"
    yield_volatility = round(0.08 + _hash_ratio(volatility_seed) * 0.18, 3)
    yield_mean_index = round(0.85 + _hash_ratio(trend_seed) * 0.35, 3)
    trend_value = _hash_ratio(f"{trend_seed}:direction")
    if trend_value < 0.33:
        yield_trend = "queda"
    elif trend_value < 0.66:
        yield_trend = "estavel"
    else:
        yield_trend = "alta"

    territorial_context = territorial_context_override or _build_fallback_territorial_context(spatial_context)
    soil_context = get_soil_context(spatial_context)
    territorial_context = _merge_soil_with_territory(territorial_context, soil_context)

    return {
        "culture": culture,
        "culture_label": culture_raw.strip().lower(),
        "sowing_date": sowing_date.isoformat(),
        "crop_stage": crop_stage,
        "irrigated": irrigated,
        "zarc_flag": zarc_flag,
        "zarc_context": zarc_context,
        "culture_profile": profile,
        "historical_yield_context": {
            "yield_mean_index": yield_mean_index,
            "yield_volatility": yield_volatility,
            "yield_trend": yield_trend,
        },
        "soil_context": soil_context,
        "territorial_context": territorial_context,
    }
