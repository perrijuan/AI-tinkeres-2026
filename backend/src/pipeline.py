from datetime import date, datetime
from typing import Any

from src.features.agro_context import get_agro_context
from src.features.map_layer import build_map_layer
from src.features.response_builder import build_frontend_response
from src.ingest.climate_forecast import get_climate_forecast
from src.ingest.territorial_context import get_territorial_context
from src.ingest.spatial_context import derive_spatial_context
from src.scoring.alerts import generate_alerts_and_recommendations
from src.scoring.risk import calculate_risk_score
from src.utils.io import model_to_dict


def _coerce_input_types(inputs: dict[str, Any]) -> dict[str, Any]:
    if isinstance(inputs.get("analysis_timestamp"), str):
        raw_ts = inputs["analysis_timestamp"]
        inputs["analysis_timestamp"] = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
    if isinstance(inputs.get("sowing_date"), str):
        inputs["sowing_date"] = date.fromisoformat(inputs["sowing_date"])
    return inputs


def analyze_field(payload: Any) -> dict[str, Any]:
    inputs = _coerce_input_types(model_to_dict(payload))
    spatial_context = derive_spatial_context(inputs)
    climate_data = get_climate_forecast(
        spatial_context,
        inputs["analysis_timestamp"],
        geometry=inputs.get("geometry"),
    )
    territorial_context = get_territorial_context(
        geometry=inputs["geometry"],
        spatial_context=spatial_context,
        analysis_timestamp=inputs["analysis_timestamp"],
    )
    agro_context = get_agro_context(
        inputs,
        spatial_context,
        territorial_context_override=territorial_context,
    )
    risk_result = calculate_risk_score(climate_data, agro_context)
    alert_data = generate_alerts_and_recommendations(risk_result, climate_data, agro_context)
    map_layer = build_map_layer(inputs, risk_result)

    return build_frontend_response(
        inputs=inputs,
        spatial_context=spatial_context,
        climate_data=climate_data,
        agro_context=agro_context,
        risk_result=risk_result,
        alert_data=alert_data,
        map_layer=map_layer,
    )
