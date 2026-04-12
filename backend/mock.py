CULTURE_LABELS = {
    "soja": "Soja",
    "milho": "Milho",
    "algodao": "Algodão",
    "arroz": "Arroz",
    "feijao": "Feijão",
    "trigo": "Trigo",
    "cana": "Cana-de-açúcar",
    "girassol": "Girassol",
    "sorgo": "Sorgo",
    "amendoim": "Amendoim",
}

RISK_COLORS = {
    "baixo":    ("#22c55e", "#15803d"),
    "moderado": ("#f59e0b", "#b45309"),
    "alto":     ("#ef4444", "#991b1b"),
    "crítico":  ("#7f1d1d", "#450a0a"),
}


def get_mock_analysis(payload: dict | None = None) -> dict:
    # Extrai dados reais do payload quando disponível
    cultura_id   = (payload or {}).get("cultura", "soja")
    cultura_nome = CULTURE_LABELS.get(cultura_id, cultura_id.title())
    area_ha      = float((payload or {}).get("poligono", {}).get("areaHa", 342.7))
    nome         = (payload or {}).get("nome", "Fazenda Santa Fé")
    timestamp    = (payload or {}).get("timestamp", "2026-04-12T14:30:00Z")

    centroide    = (payload or {}).get("poligono", {}).get("centroide", {"lat": -12.543, "lng": -55.712})
    geojson      = (payload or {}).get("poligono", {}).get("geoJSON", {}).get("geometry", {
        "type": "Polygon",
        "coordinates": [[
            [-55.712, -12.543], [-55.698, -12.543],
            [-55.698, -12.531], [-55.712, -12.531],
            [-55.712, -12.543],
        ]],
    })

    # Score e nível de risco (fixo no mock)
    risk_score = 78
    risk_level = "alto"
    fill_color, stroke_color = RISK_COLORS[risk_level]

    return {
        "field_info": {
            "field_id": f"talhao_{cultura_id}_01",
            "property_name": nome,
            "culture": cultura_id,
            "municipio": "Sorriso",
            "uf": "MT",
            "area_ha": round(area_ha, 1),
            "irrigated": False,
            "sowing_date": "2025-10-15",
            "crop_stage": "enchimento_de_graos",
        },
        "summary": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "primary_alert": "Risco elevado de estresse hídrico nos próximos 10 dias.",
            "recommended_action": "Priorizar monitoramento e manejo hídrico nos talhões mais sensíveis.",
            "analysis_timestamp": timestamp,
            "forecast_run_timestamp": "2026-04-12T12:00:00Z",
        },
        "metrics": {
            "precip_forecast_7d_mm": 11.2,
            "precip_forecast_14d_mm": 28.4,
            "temp_mean_7d_c": 29.3,
            "temp_max_7d_c": 36.8,
            "humidity_mean_7d_pct": 54.1,
            "wind_mean_7d_ms": 3.4,
        },
        "risk_flags": {
            "dry_risk_flag": True,
            "heat_risk_flag": True,
            "outside_zarc_flag": True,
            "vegetation_stress_flag": True,
        },
        "data_sources": {
            "climate": {
                "provider": "Open-Meteo",
                "model": "GFS + ECMWF blend",
                "last_update": "2026-04-12T12:00:00Z",
                "coverage": "14 dias",
                "signals": [
                    f"Precipitação acumulada 7d: 11.2 mm (abaixo da média histórica de 38 mm)",
                    "Temperatura máxima: 36.8 °C (acima da média de 31 °C para o período)",
                    "Umidade relativa média: 54% (abaixo de 65%, limiar de conforto hídrico)",
                    "Vento médio: 3.4 m/s (favorece maior evapotranspiração)",
                ],
            },
            "satellite": {
                "provider": "Sentinel-2 / MODIS",
                "last_image": "2026-04-10T10:22:00Z",
                "cloud_cover_pct": 8,
                "signals": [
                    f"NDVI atual: 0.52 (queda de 0.11 em relação à média histórica para {cultura_nome})",
                    "EVI: 0.44 (indicador de dossel sob pressão hídrica)",
                    "LST (temperatura de superfície): 38.2 °C (2.6 °C acima da média regional)",
                    "Anomalia de umidade do solo: -0.18 (seco em relação à climatologia)",
                ],
                "ndvi_timeseries": [
                    {"date": "2026-03-01", "ndvi": 0.71},
                    {"date": "2026-03-11", "ndvi": 0.68},
                    {"date": "2026-03-21", "ndvi": 0.63},
                    {"date": "2026-04-01", "ndvi": 0.58},
                    {"date": "2026-04-10", "ndvi": 0.52},
                ],
            },
            "zarc": {
                "provider": "MAPA — Zoneamento Agrícola de Risco Climático",
                "reference_year": 2025,
                "signals": [
                    f"Município de Sorriso está dentro da janela ZARC para {cultura_nome} grupo 6.1–6.5 até 15/11",
                    "Data de plantio (15/10) está dentro da janela recomendada",
                    "Precipitação acumulada 14d (28.4 mm) abaixo do limiar ZARC de 40 mm para este estágio",
                    "Risco ZARC calculado para o município: Moderado (classe 3)",
                ],
                "zarc_class": 3,
                "zarc_label": "Moderado",
                "planting_window_start": "2025-10-01",
                "planting_window_end": "2025-11-30",
                "planting_within_window": True,
            },
            "historical": {
                "provider": "ERA5 / IBGE",
                "period": "1991–2020",
                "signals": [
                    f"Precipitação média histórica para abril: 127 mm (tendência de déficit para a área de {area_ha:.0f} ha)",
                    "Frequência histórica de veranicos em abril: 34% dos anos",
                    f"Produtividade média histórica de {cultura_nome} em Sorriso: 58 sc/ha",
                    "Anos com perfil climático similar (2016, 2020) tiveram queda média de 18% na produtividade",
                ],
            },
        },
        "forecast_timeseries": [
            {"forecast_time": "2026-04-12T00:00:00Z", "precip_mm": 0.0,  "temp_c": 29.1, "humidity_pct": 52.0},
            {"forecast_time": "2026-04-13T00:00:00Z", "precip_mm": 0.0,  "temp_c": 30.4, "humidity_pct": 50.1},
            {"forecast_time": "2026-04-14T00:00:00Z", "precip_mm": 2.1,  "temp_c": 28.7, "humidity_pct": 57.3},
            {"forecast_time": "2026-04-15T00:00:00Z", "precip_mm": 4.8,  "temp_c": 27.2, "humidity_pct": 63.8},
            {"forecast_time": "2026-04-16T00:00:00Z", "precip_mm": 1.3,  "temp_c": 28.9, "humidity_pct": 58.2},
            {"forecast_time": "2026-04-17T00:00:00Z", "precip_mm": 0.0,  "temp_c": 31.5, "humidity_pct": 51.0},
            {"forecast_time": "2026-04-18T00:00:00Z", "precip_mm": 3.0,  "temp_c": 29.8, "humidity_pct": 55.4},
            {"forecast_time": "2026-04-19T00:00:00Z", "precip_mm": 0.0,  "temp_c": 32.1, "humidity_pct": 49.7},
            {"forecast_time": "2026-04-20T00:00:00Z", "precip_mm": 0.0,  "temp_c": 33.4, "humidity_pct": 47.3},
            {"forecast_time": "2026-04-21T00:00:00Z", "precip_mm": 0.0,  "temp_c": 34.2, "humidity_pct": 46.1},
            {"forecast_time": "2026-04-22T00:00:00Z", "precip_mm": 0.0,  "temp_c": 35.0, "humidity_pct": 45.8},
            {"forecast_time": "2026-04-23T00:00:00Z", "precip_mm": 5.2,  "temp_c": 30.3, "humidity_pct": 60.2},
            {"forecast_time": "2026-04-24T00:00:00Z", "precip_mm": 8.1,  "temp_c": 27.8, "humidity_pct": 67.5},
            {"forecast_time": "2026-04-25T00:00:00Z", "precip_mm": 3.9,  "temp_c": 28.5, "humidity_pct": 64.0},
        ],
        "map_layer": {
            "geometry": geojson,
            "fill_color": fill_color,
            "stroke_color": stroke_color,
            "tooltip_summary": f"Risco {risk_level} | {cultura_nome} | {area_ha:.0f} ha | 11 mm/7d | 36.8 °C max",
        },
        "copilot_response": {
            "summary": f"A área de {cultura_nome} ({area_ha:.0f} ha) está em risco alto de estresse hídrico. A combinação de baixa precipitação prevista, temperaturas acima de 36 °C e queda de NDVI nos últimos 40 dias indica pressão no estágio de enchimento de grãos.",
            "why": [
                "Precipitação prevista de apenas 11.2 mm nos próximos 7 dias, muito abaixo da média histórica de 38 mm.",
                f"Temperatura máxima de 36.8 °C acima do limite de conforto térmico da {cultura_nome} (32 °C), aumentando a evapotranspiração.",
                "NDVI caiu de 0.71 para 0.52 nas últimas seis semanas, indicando deterioração do dossel vegetativo.",
                "Precipitação acumulada em 14 dias (28.4 mm) abaixo do limiar ZARC de 40 mm para este estágio da cultura.",
            ],
            "action": f"Intensifique o monitoramento nos próximos 7 dias nos {area_ha:.0f} ha cadastrados. Se a precipitação não ocorrer até 19/04, avalie a antecipação da colheita nos blocos mais afetados para reduzir perdas.",
        },
    }
