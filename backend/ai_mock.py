"""
Gera dados de análise agroclimática realistas via Gemini.

Recebe o payload do frontend (cultura, área, coordenadas) e pede ao Gemini
que produza métricas climáticas, timeseries, flags de risco e insights
coerentes com a região, cultura e época do ano.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import google.generativeai as genai

from mock import CULTURE_LABELS, RISK_COLORS


def _build_prompt(payload: dict) -> str:
    cultura_id  = payload.get("cultura", "soja")
    cultura     = CULTURE_LABELS.get(cultura_id, cultura_id.title())
    area_ha     = float((payload.get("poligono") or {}).get("areaHa", 100))
    nome        = payload.get("nome", "Fazenda")
    centroide   = (payload.get("poligono") or {}).get("centroide", {"lat": -12.5, "lng": -55.7})
    today       = payload.get("timestamp", datetime.utcnow().isoformat() + "Z")[:10]

    # Datas para a timeseries de previsão (14 dias)
    forecast_dates = [
        (datetime.fromisoformat(today) + timedelta(days=i)).strftime("%Y-%m-%dT00:00:00Z")
        for i in range(14)
    ]

    # Datas para NDVI (5 pontos, ~10 dias entre cada um, retroativos)
    ndvi_dates = [
        (datetime.fromisoformat(today) - timedelta(days=40 - i * 10)).strftime("%Y-%m-%d")
        for i in range(5)
    ]

    return f"""Você é um sistema agroclimático especialista em culturas do Brasil.
Gere uma análise de risco realista para o campo abaixo.
Use os dados climáticos e agronômicos típicos da região e época do ano.

=== CAMPO ===
Cultura    : {cultura}
Área       : {area_ha:.1f} ha
Propriedade: {nome}
Coordenadas: lat {centroide.get('lat', -12.5):.4f}, lng {centroide.get('lng', -55.7):.4f}
Data       : {today}

Responda SOMENTE com JSON válido, sem markdown, sem texto fora do JSON.

{{
  "municipio": "<município mais próximo das coordenadas>",
  "uf": "<sigla do estado>",
  "crop_stage": "<germinacao|vegetativo|florescimento|enchimento_de_graos|maturacao>",
  "risk_score": <inteiro 0–100 coerente com os dados>,
  "risk_level": "<baixo|moderado|alto|crítico>",
  "primary_alert": "<alerta principal em 1 frase curta>",
  "recommended_action": "<ação recomendada em 1 frase>",
  "metrics": {{
    "precip_forecast_7d_mm": <número>,
    "precip_forecast_14d_mm": <número>,
    "temp_mean_7d_c": <número>,
    "temp_max_7d_c": <número>,
    "humidity_mean_7d_pct": <número>,
    "wind_mean_7d_ms": <número>
  }},
  "risk_flags": {{
    "dry_risk_flag": <true|false>,
    "heat_risk_flag": <true|false>,
    "outside_zarc_flag": <true|false>,
    "vegetation_stress_flag": <true|false>
  }},
  "climate_signals": [
    "<sinal climático 1>",
    "<sinal climático 2>",
    "<sinal climático 3>",
    "<sinal climático 4>"
  ],
  "satellite_signals": [
    "<sinal de satélite 1>",
    "<sinal de satélite 2>",
    "<sinal de satélite 3>",
    "<sinal de satélite 4>"
  ],
  "zarc_signals": [
    "<sinal ZARC 1 específico para {cultura}>",
    "<sinal ZARC 2>",
    "<sinal ZARC 3>",
    "<sinal ZARC 4>"
  ],
  "historical_signals": [
    "<comparativo histórico 1>",
    "<comparativo histórico 2>",
    "<comparativo histórico 3>",
    "<comparativo histórico 4>"
  ],
  "cloud_cover_pct": <inteiro 0–100>,
  "zarc_class": <inteiro 1–5>,
  "zarc_label": "<Baixo|Moderado|Alto|Muito Alto>",
  "planting_within_window": <true|false>,
  "last_satellite_image": "<ISO datetime de imagem recente aproximada>",
  "forecast_timeseries": [
    {forecast_timeseries_str(forecast_dates)}
  ],
  "ndvi_timeseries": [
    {ndvi_timeseries_str(ndvi_dates)}
  ],
  "copilot_summary": "<2 frases descrevendo o cenário>",
  "copilot_why": [
    "<fator 1>",
    "<fator 2>",
    "<fator 3>"
  ],
  "copilot_action": "<recomendação prática em 1-2 frases>"
}}"""


def forecast_timeseries_str(dates: list[str]) -> str:
    entries = [
        f'{{"forecast_time": "{d}", "precip_mm": <número>, "temp_c": <número>, "humidity_pct": <número>}}'
        for d in dates
    ]
    return ",\n    ".join(entries)


def ndvi_timeseries_str(dates: list[str]) -> str:
    entries = [f'{{"date": "{d}", "ndvi": <0.0–1.0>}}' for d in dates]
    return ",\n    ".join(entries)


def generate_ai_analysis(payload: dict) -> dict:
    """
    Gera a análise completa via Gemini e monta o dict no formato esperado pelo frontend.
    Lança exceção em caso de falha — o router deve capturar e usar o mock como fallback.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY não configurada.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

    prompt   = _build_prompt(payload)
    response = model.generate_content(prompt)

    raw = response.text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    ai = json.loads(raw)

    # ── Monta o dict no formato completo esperado pelo frontend ──

    cultura_id  = payload.get("cultura", "soja")
    cultura     = CULTURE_LABELS.get(cultura_id, cultura_id.title())
    area_ha     = float((payload.get("poligono") or {}).get("areaHa", 100))
    nome        = payload.get("nome", "Fazenda")
    timestamp   = payload.get("timestamp", datetime.utcnow().isoformat() + "Z")
    geojson     = (payload.get("poligono") or {}).get("geoJSON", {}).get("geometry", {
        "type": "Polygon",
        "coordinates": [[
            [-55.712, -12.543], [-55.698, -12.543],
            [-55.698, -12.531], [-55.712, -12.531],
            [-55.712, -12.543],
        ]],
    })

    risk_level              = ai.get("risk_level", "moderado")
    fill_color, stroke_color = RISK_COLORS.get(risk_level, RISK_COLORS["moderado"])

    return {
        "field_info": {
            "field_id":      f"talhao_{cultura_id}_01",
            "property_name": nome,
            "culture":       cultura_id,
            "municipio":     ai.get("municipio", "—"),
            "uf":            ai.get("uf", "—"),
            "area_ha":       round(area_ha, 1),
            "irrigated":     False,
            "sowing_date":   "2025-10-15",
            "crop_stage":    ai.get("crop_stage", "vegetativo"),
        },
        "summary": {
            "risk_score":              ai.get("risk_score", 50),
            "risk_level":              risk_level,
            "primary_alert":           ai.get("primary_alert", ""),
            "recommended_action":      ai.get("recommended_action", ""),
            "analysis_timestamp":      timestamp,
            "forecast_run_timestamp":  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "metrics":    ai.get("metrics", {}),
        "risk_flags": ai.get("risk_flags", {}),
        "data_sources": {
            "climate": {
                "provider":    "Open-Meteo",
                "model":       "GFS + ECMWF blend",
                "last_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "coverage":    "14 dias",
                "signals":     ai.get("climate_signals", []),
            },
            "satellite": {
                "provider":        "Sentinel-2 / MODIS",
                "last_image":      ai.get("last_satellite_image", timestamp),
                "cloud_cover_pct": ai.get("cloud_cover_pct", 10),
                "signals":         ai.get("satellite_signals", []),
                "ndvi_timeseries": ai.get("ndvi_timeseries", []),
            },
            "zarc": {
                "provider":               "MAPA — Zoneamento Agrícola de Risco Climático",
                "reference_year":         2025,
                "signals":                ai.get("zarc_signals", []),
                "zarc_class":             ai.get("zarc_class", 3),
                "zarc_label":             ai.get("zarc_label", "Moderado"),
                "planting_window_start":  "2025-10-01",
                "planting_window_end":    "2025-11-30",
                "planting_within_window": ai.get("planting_within_window", True),
            },
            "historical": {
                "provider": "ERA5 / IBGE",
                "period":   "1991–2020",
                "signals":  ai.get("historical_signals", []),
            },
        },
        "forecast_timeseries": ai.get("forecast_timeseries", []),
        "copilot_response": {
            "summary": ai.get("copilot_summary", ""),
            "why":     ai.get("copilot_why", []),
            "action":  ai.get("copilot_action", ""),
        },
        "map_layer": {
            "geometry":        geojson,
            "fill_color":      fill_color,
            "stroke_color":    stroke_color,
            "tooltip_summary": (
                f"Risco {risk_level} | {cultura} | {area_ha:.0f} ha | "
                f"{ai.get('metrics', {}).get('precip_forecast_7d_mm', '—')} mm/7d | "
                f"{ai.get('metrics', {}).get('temp_max_7d_c', '—')} °C max"
            ),
        },
    }
