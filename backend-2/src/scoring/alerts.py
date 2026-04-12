from typing import Any


def _build_why_list(risk_flags: dict[str, bool], climate_data: dict[str, Any], agro_context: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if risk_flags["dry_risk_flag"]:
        reasons.append(
            f"Baixa precipitação prevista na janela de 7 dias ({climate_data['precip_forecast_7d_mm']} mm)."
        )
    if risk_flags["heat_risk_flag"]:
        reasons.append(f"Temperaturas máximas elevadas ({climate_data['temp_max_7d_c']} °C) para a cultura.")
    if risk_flags["outside_zarc_flag"]:
        reasons.append("Data de plantio fora da janela preferencial do ZARC para esta cultura.")
    if risk_flags["vegetation_stress_flag"]:
        reasons.append("Sinais territoriais indicam maior vulnerabilidade a estresse vegetativo.")
    if not reasons:
        reasons.append("Condições climáticas previstas dentro de faixa aceitável para o curto prazo.")
    return reasons


def generate_alerts_and_recommendations(
    risk_result: dict[str, Any],
    climate_data: dict[str, Any],
    agro_context: dict[str, Any],
) -> dict[str, Any]:
    risk_score = risk_result["risk_score"]
    risk_level = risk_result["risk_level"]
    risk_flags = risk_result["risk_flags"]

    if risk_level in {"alto", "crítico"} and risk_flags["dry_risk_flag"]:
        primary_alert = "Risco elevado de estresse hídrico nos próximos 10 dias."
    elif risk_level in {"alto", "crítico"} and risk_flags["heat_risk_flag"]:
        primary_alert = "Risco elevado de estresse térmico nos próximos dias."
    elif risk_level == "moderado":
        primary_alert = "Risco moderado: acompanhar evolução climática e sinais de campo."
    else:
        primary_alert = "Risco baixo no curto prazo para a área analisada."

    if risk_flags["dry_risk_flag"] and not agro_context["irrigated"]:
        recommended_action = "Priorizar monitoramento e irrigação nos talhões mais sensíveis."
    elif risk_flags["dry_risk_flag"] and agro_context["irrigated"]:
        recommended_action = "Revisar lâmina e turno de irrigação para mitigar estresse hídrico."
    elif risk_flags["heat_risk_flag"]:
        recommended_action = "Ajustar manejo e intensificar monitoramento em horários de pico de calor."
    elif risk_flags["outside_zarc_flag"]:
        recommended_action = "Reavaliar janela de manejo e reforçar monitoramento por estar fora do ZARC."
    else:
        recommended_action = "Manter monitoramento de rotina e revisar análise a cada novo run de forecast."

    why_list = _build_why_list(risk_flags, climate_data, agro_context)
    culture = agro_context["culture_label"]

    copilot_response = {
        "summary": f"Esta área apresenta risco {risk_level} para a cultura {culture} no curto prazo.",
        "why": why_list,
        "action": recommended_action,
    }

    return {
        "primary_alert": primary_alert,
        "recommended_action": recommended_action,
        "copilot_response": copilot_response,
        "risk_score": risk_score,
    }

