from typing import Any

from src.utils.time import to_iso_z


def _build_data_sources(
    climate_data: dict[str, Any],
    climate_history: dict[str, Any] | None,
    agro_context: dict[str, Any],
) -> dict[str, Any]:
    territory = agro_context["territorial_context"]
    zarc_context = agro_context.get("zarc_context", {})
    soil_context = agro_context.get("soil_context", {})

    satellite_signals = list(territory.get("signals", []))
    if territory.get("ndvi") is not None:
        satellite_signals.append(f"NDVI medio recente: {territory['ndvi']}.")
    if territory.get("evi") is not None:
        satellite_signals.append(f"EVI medio recente: {territory['evi']}.")
    if territory.get("lst_c") is not None:
        satellite_signals.append(f"LST medio recente: {territory['lst_c']} C.")
    if territory.get("ndvi_trend"):
        satellite_signals.append(f"Tendencia NDVI recente: {territory['ndvi_trend']}.")
    if territory.get("ndvi_delta_30d") is not None:
        satellite_signals.append(f"Delta NDVI recente: {territory['ndvi_delta_30d']}.")
    if territory.get("ndvi_anomaly") is not None:
        satellite_signals.append(f"Anomalia NDVI: {territory['ndvi_anomaly']}.")

    historical = agro_context["historical_yield_context"]
    historical_signals = list(historical.get("signals", []))
    if not historical_signals:
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
        "climate_history": {
            "provider": (climate_history or {}).get("provider", "SafraViva Climate History"),
            "dataset": (climate_history or {}).get("dataset", "mvp"),
            "window_start": (climate_history or {}).get("window_start"),
            "window_end": (climate_history or {}).get("window_end"),
            "latest_observed_date": (climate_history or {}).get("latest_observed_date"),
            "data_lag_days": (climate_history or {}).get("data_lag_days"),
            "precip_observed_7d_mm": (climate_history or {}).get("precip_observed_7d_mm"),
            "precip_observed_30d_mm": (climate_history or {}).get("precip_observed_30d_mm"),
            "precip_climatology_30d_mm": (climate_history or {}).get("precip_climatology_30d_mm"),
            "precip_anomaly_30d_mm": (climate_history or {}).get("precip_anomaly_30d_mm"),
            "precip_anomaly_30d_pct": (climate_history or {}).get("precip_anomaly_30d_pct"),
            "dry_days_30d": (climate_history or {}).get("dry_days_30d"),
            "timeseries_30d": (climate_history or {}).get("timeseries_30d", []),
            "signals": (climate_history or {}).get("signals", []),
        },
        "satellite": {
            "provider": territory.get("provider", "SafraViva Territory"),
            "last_image": territory.get("last_image") or climate_data["forecast_run_timestamp"],
            "cloud_cover_pct": territory.get("cloud_cover_pct") or 0.0,
            "ndvi_trend": territory.get("ndvi_trend", "stable"),
            "ndvi_delta_30d": territory.get("ndvi_delta_30d", 0.0),
            "ndvi_anomaly": territory.get("ndvi_anomaly", 0.0),
            "vegetation_mismatch_flag": bool(territory.get("vegetation_mismatch_flag", False)),
            "ndvi_heatmap": territory.get("ndvi_heatmap", {"type": "FeatureCollection", "features": []}),
            "ndvi_heatmap_meta": territory.get("ndvi_heatmap_meta", {"cell_count": 0}),
            "signals": satellite_signals,
            "ndvi_timeseries": territory.get("ndvi_timeseries", []),
        },
        "soil": {
            "provider": soil_context.get("provider", "BDSolos/Embrapa"),
            "source": soil_context.get("source", "fallback"),
            "interpretation_scope": soil_context.get("interpretation_scope", "estrutural"),
            "temporal_nature": soil_context.get("temporal_nature", "historico_heterogeneo"),
            "short_term_reliability": soil_context.get("short_term_reliability", "baixa"),
            "soil_quality_index": soil_context.get("soil_quality_index", 0.5),
            "soil_quality_label": soil_context.get("soil_quality_label", "media"),
            "soil_good_flag": bool(soil_context.get("soil_good_flag", False)),
            "confidence_index": soil_context.get("confidence_index", 0.3),
            "sample_count": soil_context.get("sample_count", 0),
            "nearest_sample_km": soil_context.get("nearest_sample_km"),
            "signals": soil_context.get("signals", []),
        },
        "zarc": {
            "provider": zarc_context.get("provider", "SafraViva ZARC"),
            "zarc_class": zarc_context.get("zarc_class", 3),
            "zarc_label": zarc_context.get("zarc_label", "Moderado"),
            "planting_within_window": bool(agro_context["zarc_flag"]),
            "signals": zarc_context.get("signals", []),
        },
        "historical": {
            "provider": historical.get("provider", "IBGE/PAM"),
            "source": historical.get("source", "unknown"),
            "scope": historical.get("scope", "baseline municipal"),
            "period_start": historical.get("period_start"),
            "period_end": historical.get("period_end"),
            "yield_mean_index": historical.get("yield_mean_index"),
            "yield_volatility": historical.get("yield_volatility"),
            "yield_trend": historical.get("yield_trend"),
            "signals": historical_signals,
        },
    }


def build_frontend_response(
    inputs: dict[str, Any],
    spatial_context: dict[str, Any],
    climate_data: dict[str, Any],
    climate_history: dict[str, Any] | None,
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
        "data_sources": _build_data_sources(climate_data, climate_history, agro_context),
        "forecast_timeseries": climate_data["forecast_timeseries"],
        "map_layer": map_layer,
        "copilot_response": alert_data["copilot_response"],
    }
