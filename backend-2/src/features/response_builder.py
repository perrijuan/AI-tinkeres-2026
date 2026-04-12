from typing import Any

from src.utils.time import to_iso_z


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
        },
        "risk_flags": risk_result["risk_flags"],
        "forecast_timeseries": climate_data["forecast_timeseries"],
        "map_layer": map_layer,
        "copilot_response": alert_data["copilot_response"],
    }
