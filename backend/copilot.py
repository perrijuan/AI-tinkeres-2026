"""
Camada de interpretação com Gemini.

Recebe os dados já processados (métricas climáticas, score de risco,
flags, contexto agrícola) e gera os insights em linguagem natural.
"""

from __future__ import annotations

import json
import os

import google.generativeai as genai


def _build_prompt(analysis: dict) -> str:
    fi = analysis["field_info"]
    sm = analysis["summary"]
    mt = analysis["metrics"]
    fl = analysis["risk_flags"]
    ds = analysis["data_sources"]

    flags_text = []
    if fl["dry_risk_flag"]:
        flags_text.append(f"seca: apenas {mt['precip_forecast_7d_mm']} mm previstos em 7 dias")
    if fl["heat_risk_flag"]:
        flags_text.append(f"calor excessivo: temperatura máxima de {mt['temp_max_7d_c']} °C")
    if fl["outside_zarc_flag"]:
        flags_text.append(f"precipitação 14d abaixo do limiar ZARC ({mt['precip_forecast_14d_mm']} mm)")
    if fl["vegetation_stress_flag"]:
        flags_text.append("estresse de vegetação detectado via satélite")

    satellite_signals = "\n".join(f"  - {s}" for s in ds["satellite"]["signals"])
    zarc_signals      = "\n".join(f"  - {s}" for s in ds["zarc"]["signals"])
    hist_signals      = "\n".join(f"  - {s}" for s in ds["historical"]["signals"])

    return f"""Você é o copiloto agroclimático da SafraViva.
Analise os dados abaixo e gere um diagnóstico claro e acionável para o produtor.

Responda SOMENTE com JSON válido, sem markdown, sem texto fora do JSON.
Estrutura obrigatória:
{{
  "summary": "<1-2 frases descrevendo o cenário climático da área>",
  "why": ["<fator 1>", "<fator 2>", "<fator 3>"],
  "action": "<1-2 frases de recomendação prática>"
}}

--- DADOS DA ANÁLISE ---

Propriedade: {fi['property_name']}
Cultura: {fi['culture']} | Área: {fi['area_ha']} ha | Município: {fi['municipio']}, {fi['uf']}
Irrigado: {"Sim" if fi['irrigated'] else "Não"} | Estágio: {fi.get('crop_stage', 'não informado')}

Score de risco: {sm['risk_score']}/100 ({sm['risk_level']})

Métricas climáticas:
  - Precipitação 7 dias: {mt['precip_forecast_7d_mm']} mm
  - Precipitação 14 dias: {mt['precip_forecast_14d_mm']} mm
  - Temperatura máxima 7d: {mt['temp_max_7d_c']} °C
  - Temperatura média 7d: {mt['temp_mean_7d_c']} °C
  - Umidade média 7d: {mt['humidity_mean_7d_pct']}%
  - Vento médio 7d: {mt['wind_mean_7d_ms']} m/s

Fatores de risco ativos:
{chr(10).join(f'  - {f}' for f in flags_text) if flags_text else '  - nenhum'}

Sinais de satélite:
{satellite_signals}

Contexto ZARC:
{zarc_signals}

Histórico:
{hist_signals}
"""


def generate_copilot_response(analysis: dict) -> dict:
    """
    Recebe o dict completo de análise e retorna um novo copilot_response
    gerado pelo Gemini.

    Substitui apenas o campo copilot_response — todo o resto do analysis
    permanece intacto.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY não configurada.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

    prompt = _build_prompt(analysis)
    response = model.generate_content(prompt)

    raw = response.text.strip()

    # Remove blocos de código markdown se o modelo os incluir
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    parsed = json.loads(raw)

    return {
        "summary": parsed["summary"],
        "why": parsed["why"],
        "action": parsed["action"],
    }
