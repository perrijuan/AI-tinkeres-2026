# API Contract (MVP)

## Endpoint

- `POST /api/v1/analysis`

## Entrada

```json
{
  "field_id": "talhao_01",
  "property_name": "Fazenda Exemplo",
  "culture": "soja",
  "sowing_date": "2026-10-15",
  "crop_stage": null,
  "irrigated": false,
  "analysis_timestamp": "2026-04-11T20:30:00Z",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[ -55.81, -12.43 ], [ -55.74, -12.43 ], [ -55.74, -12.49 ], [ -55.81, -12.49 ], [ -55.81, -12.43 ]]]
  }
}
```

## Saída

```json
{
  "field_info": {},
  "summary": {},
  "metrics": {},
  "risk_flags": {},
  "data_sources": {},
  "forecast_timeseries": [],
  "map_layer": {},
  "copilot_response": {}
}
```

## Funções implementadas

- `derive_spatial_context(inputs)`
- `get_climate_forecast(spatial_context, analysis_timestamp)`
- `get_agro_context(inputs, spatial_context)`
- `calculate_risk_score(climate_data, agro_context)`
- `generate_alerts_and_recommendations(risk_result, climate_data, agro_context)`
- `build_map_layer(inputs, risk_result)`
- `build_frontend_response(...)`
