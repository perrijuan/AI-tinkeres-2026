from typing import Any

from src.utils.time import to_iso_z


def _build_data_sources(climate_data: dict[str, Any], agro_context: dict[str, Any]) -> dict[str, Any]:
    territory = agro_context["territorial_context"]
    zarc_context = agro_context.get("zarc_context", {})

    satellite_signals = list(territory.get("signals", []))
    if territory.get("ndvi") is not None:
        satellite_signals.append(f"NDVI medio recente: {territory['ndvi']}.")
    if territory.get("evi") is not None:
        satellite_signals.append(f"EVI medio recente: {territory['evi']}.")
    if territory.get("lst_c") is not None:
        satellite_signals.append(f"LST medio recente: {territory['lst_c']} C.")

    historical = agro_context["historical_yield_context"]
    historical_signals = [
        f"Indice medio de produtividade historica: {historical['yield_mean_index']}.",
        f"Volatilidade historica de produtividade: {historical['yield_volatility']}.",
        f"Tendencia historica observada: {historical['yield_trend']}.",
    ]

    return {
        "climate": {
            "provider": climate_data.get("provider", "SafraViva Climate"),
            "model": climate_data.get("model", "mvp"),
            "coverage": "14 dias",
            "signals": climate_data.get("signals", []),
        },
        "satellite": {
            "provider": territory.get("provider", "SafraViva Territory"),
            "last_image": territory.get("last_image") or climate_data["forecast_run_timestamp"],
            "cloud_cover_pct": territory.get("cloud_cover_pct") or 0.0,
            "signals": satellite_signals,
            "ndvi_timeseries": territory.get("ndvi_timeseries", []),
        },
        "zarc": {
            "provider": zarc_context.get("provider", "SafraViva ZARC"),
            "zarc_class": zarc_context.get("zarc_class", 3),
            "zarc_label": zarc_context.get("zarc_label", "Moderado"),
            "planting_within_window": bool(agro_context["zarc_flag"]),
            "signals": zarc_context.get("signals", []),
        },
        "historical": {
            "provider": "IBGE/PAM (placeholder MVP)",
            "period": "baseline municipal",
            "signals": historical_signals,
        },
    }


def build_frontend_response(
    inputs: dict[str, Any],
    spatial_context: dict[str, Any],
    climate_data: dict[str, Any],
    agro_context: dict[str, Any],
    risk_result: dict[str, Any],
    alert_data: dict[str, Any],
    map_layer: dict[str, Any],
) -> dict[str, Any]:
    return {
        "field_info": {
            "field_id": inputs.get("field_id"),
            "property_name": inputs.get("property_name"),
            "culture": agro_context["culture_label"],
            "municipio": spatial_context["municipio"],
            "uf": spatial_context["uf"],
            "area_ha": spatial_context["area_ha"],
            "irrigated": agro_context["irrigated"],
            "sowing_date": agro_context["sowing_date"],
            "crop_stage": agro_context["crop_stage"],
        },
        "summary": {
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "primary_alert": alert_data["primary_alert"],
            "recommended_action": alert_data["recommended_action"],
            "analysis_timestamp": to_iso_z(inputs["analysis_timestamp"]),
            "forecast_run_timestamp": climate_data["forecast_run_timestamp"],
        },
        "metrics": {
            "precip_forecast_7d_mm": climate_data["precip_forecast_7d_mm"],
            "precip_forecast_14d_mm": climate_data["precip_forecast_14d_mm"],
            "temp_mean_7d_c": climate_data["temp_mean_7d_c"],
            "temp_max_7d_c": climate_data["temp_max_7d_c"],
            "humidity_mean_7d_pct": climate_data["humidity_mean_7d_pct"],
            "wind_mean_7d_ms": climate_data["wind_mean_7d_ms"],
        },
        "risk_flags": risk_result["risk_flags"],
        "data_sources": _build_data_sources(climate_data, agro_context),
        "forecast_timeseries": climate_data["forecast_timeseries"],
        "map_layer": map_layer,
        "copilot_response": alert_data["copilot_response"],
    }
