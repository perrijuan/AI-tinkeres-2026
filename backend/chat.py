"""
Gerenciamento de conversas com o copiloto SafraViva via Gemini.

Cada análise gera um conversation_id único. O histórico fica em memória
enquanto o servidor estiver rodando (MVP). Em produção substituir por Redis/DB.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime

import google.generativeai as genai

# conversation_id → { system, history, created_at }
_store: dict[str, dict] = {}


def _system_prompt(context: dict) -> str:
    fi = context.get("field_info", {})
    sm = context.get("summary", {})
    mt = context.get("metrics", {})
    fl = context.get("risk_flags", {})

    flags = []
    if fl.get("dry_risk_flag"):
        flags.append(f"risco de seca ({mt.get('precip_forecast_7d_mm', 0)} mm/7d)")
    if fl.get("heat_risk_flag"):
        flags.append(f"calor excessivo ({mt.get('temp_max_7d_c', 0)} °C máx)")
    if fl.get("outside_zarc_flag"):
        flags.append("precipitação abaixo do limiar ZARC")
    if fl.get("vegetation_stress_flag"):
        flags.append("estresse de vegetação detectado")

    return f"""Você é o copiloto agroclimático da SafraViva.
Está conversando diretamente com o produtor ou responsável pela área monitorada.
Responda sempre em português, com linguagem clara, empática e objetiva.
Baseie suas respostas nos dados da análise abaixo. Se não souber algo, seja honesto.

=== CONTEXTO DA ANÁLISE ===
Propriedade : {fi.get('property_name', 'não informado')}
Cultura     : {fi.get('culture', 'não informado')} | {fi.get('area_ha', 0)} ha
Município   : {fi.get('municipio', 'não informado')}, {fi.get('uf', 'MT')}
Estágio     : {fi.get('crop_stage', 'não informado')}
Irrigado    : {"Sim" if fi.get('irrigated') else "Não"}

Score de risco  : {sm.get('risk_score', 0)}/100 — {sm.get('risk_level', 'moderado')}
Alerta principal: {sm.get('primary_alert', '')}
Recomendação    : {sm.get('recommended_action', '')}

Métricas climáticas (próximos 7 dias):
  - Precipitação 7d : {mt.get('precip_forecast_7d_mm', 0)} mm
  - Precipitação 14d: {mt.get('precip_forecast_14d_mm', 0)} mm
  - Temp. máxima    : {mt.get('temp_max_7d_c', 0)} °C
  - Temp. média     : {mt.get('temp_mean_7d_c', 0)} °C
  - Umidade média   : {mt.get('humidity_mean_7d_pct', 0)}%
  - Vento médio     : {mt.get('wind_mean_7d_ms', 0)} m/s

Fatores de risco ativos: {', '.join(flags) if flags else 'nenhum'}
"""


def start_conversation(context: dict) -> str:
    """Cria uma nova sessão de conversa a partir do contexto da análise."""
    cid = str(uuid.uuid4())
    _store[cid] = {
        "system":     _system_prompt(context),
        "history":    [],
        "created_at": datetime.utcnow().isoformat(),
    }
    return cid


def send_message(conversation_id: str, message: str) -> dict:
    """
    Envia uma mensagem na conversa existente e retorna a resposta do Gemini.

    Retorna:
      {
        "conversation_id": str,
        "response": str,
        "history": [{"role": "user"|"assistant", "content": str}, ...]
      }
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY não configurada.")

    if conversation_id not in _store:
        raise KeyError(f"Conversa '{conversation_id}' não encontrada.")

    conv = _store[conversation_id]

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=conv["system"],
    )

    chat = model.start_chat(history=conv["history"])
    response = chat.send_message(message)

    # Persiste histórico no formato do Gemini
    conv["history"].append({"role": "user",  "parts": [message]})
    conv["history"].append({"role": "model", "parts": [response.text]})

    # Retorna no formato mais limpo pro frontend
    return {
        "conversation_id": conversation_id,
        "response": response.text,
        "history": [
            {
                "role":    "user" if h["role"] == "user" else "assistant",
                "content": h["parts"][0],
            }
            for h in conv["history"]
        ],
    }
