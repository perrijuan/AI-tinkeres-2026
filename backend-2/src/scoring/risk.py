from typing import Any


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _risk_level(score: int) -> str:
    if score < 25:
        return "baixo"
    if score < 50:
        return "moderado"
    if score < 75:
        return "alto"
    return "crítico"


def calculate_risk_score(climate_data: dict[str, Any], agro_context: dict[str, Any]) -> dict[str, Any]:
    profile = agro_context["culture_profile"]
    territorial = agro_context["territorial_context"]
    historical_yield = agro_context["historical_yield_context"]
    irrigated = agro_context["irrigated"]

    precip_7d = climate_data["precip_forecast_7d_mm"]
    temp_max_7d = climate_data["temp_max_7d_c"]
    humidity_7d = climate_data["humidity_mean_7d_pct"]
    wind_7d = climate_data["wind_mean_7d_ms"]

    precip_target = profile["ideal_precip_7d_mm"] * (0.72 if irrigated else 1.0)
    dry_deficit_ratio = max(0.0, precip_target - precip_7d) / max(1.0, precip_target)
    dry_points = _clamp(dry_deficit_ratio * 42.0, 0.0, 42.0)

    heat_threshold = profile["heat_threshold_c"] + (0.6 if irrigated else 0.0)
    heat_excess = max(0.0, temp_max_7d - heat_threshold)
    heat_points = _clamp(heat_excess * 7.2, 0.0, 26.0)

    humidity_points = 0.0
    if humidity_7d < 58:
        humidity_points = _clamp((58 - humidity_7d) * 0.35, 0.0, 8.0)

    wind_points = 0.0
    if wind_7d > 4.8:
        wind_points = _clamp((wind_7d - 4.8) * 2.2, 0.0, 7.0)

    zarc_points = 14.0 if not agro_context["zarc_flag"] else 0.0
    vegetation_stress_index = territorial["vegetation_stress_index"]
    vegetation_points = _clamp((vegetation_stress_index - 0.42) * 36.0, 0.0, 22.0)
    historical_points = _clamp(historical_yield["yield_volatility"] * 30.0, 0.0, 9.0)

    raw_score = (
        12.0
        + dry_points
        + heat_points
        + humidity_points
        + wind_points
        + zarc_points
        + vegetation_points
        + historical_points
    )

    risk_score = int(round(_clamp(raw_score, 0.0, 100.0)))
    risk_level = _risk_level(risk_score)

    dry_risk_flag = precip_7d < precip_target
    heat_risk_flag = temp_max_7d > heat_threshold
    outside_zarc_flag = not agro_context["zarc_flag"]
    vegetation_stress_flag = vegetation_stress_index >= 0.58

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_flags": {
            "dry_risk_flag": dry_risk_flag,
            "heat_risk_flag": heat_risk_flag,
            "outside_zarc_flag": outside_zarc_flag,
            "vegetation_stress_flag": vegetation_stress_flag,
        },
    }

