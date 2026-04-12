from typing import Any


def _build_why_list(
    risk_flags: dict[str, bool],
    climate_data: dict[str, Any],
    agro_context: dict[str, Any],
    climate_history: dict[str, Any] | None = None,
) -> list[str]:
    reasons: list[str] = []
    if risk_flags["dry_risk_flag"]:
        reasons.append(
            f"Baixa precipitacao prevista na janela de 7 dias ({climate_data['precip_forecast_7d_mm']} mm)."
        )
    if risk_flags["heat_risk_flag"]:
        reasons.append(f"Temperaturas maximas elevadas ({climate_data['temp_max_7d_c']} C) para a cultura.")
    if risk_flags["outside_zarc_flag"]:
        reasons.append("Data de plantio fora da janela preferencial do ZARC para esta cultura.")
    if risk_flags["vegetation_stress_flag"]:
        reasons.append("Sinais territoriais indicam maior vulnerabilidade a estresse vegetativo.")

    territorial = agro_context.get("territorial_context", {})
    if territorial.get("vegetation_mismatch_flag"):
        reasons.append("NDVI em queda mesmo com solo favoravel: risco de estresse nao esperado.")
    if territorial.get("ndvi_trend") == "decreasing":
        reasons.append("Tendencia recente do NDVI esta em queda.")
    if climate_history:
        anomaly_pct = climate_history.get("precip_anomaly_30d_pct")
        dry_days = climate_history.get("dry_days_30d")
        if anomaly_pct is not None and float(anomaly_pct) <= -20.0:
            reasons.append(f"Chuva observada em 30 dias abaixo da normal climatologica ({anomaly_pct}%).")
        if dry_days is not None and int(dry_days) >= 20:
            reasons.append(f"Alta frequencia de dias secos recentes: {int(dry_days)} dias (<1mm) em 30d.")

    if not reasons:
        reasons.append("Condicoes climaticas previstas dentro de faixa aceitavel para o curto prazo.")
    return reasons


def generate_alerts_and_recommendations(
    risk_result: dict[str, Any],
    climate_data: dict[str, Any],
    agro_context: dict[str, Any],
    climate_history: dict[str, Any] | None = None,
) -> dict[str, Any]:
    risk_score = risk_result["risk_score"]
    risk_level = risk_result["risk_level"]
    risk_flags = risk_result["risk_flags"]
    territorial = agro_context.get("territorial_context", {})

    critical_levels = {"alto", "critico", "crÃ­tico"}

    if territorial.get("vegetation_mismatch_flag") and risk_level in critical_levels:
        primary_alert = "Risco elevado de estresse vegetativo com sinal de mismatch NDVI-solo."
    elif risk_level in critical_levels and risk_flags["dry_risk_flag"]:
        primary_alert = "Risco elevado de estresse hidrico nos proximos 10 dias."
    elif risk_level in critical_levels and risk_flags["heat_risk_flag"]:
        primary_alert = "Risco elevado de estresse termico nos proximos dias."
    elif risk_level == "moderado":
        primary_alert = "Risco moderado: acompanhar evolucao climatica e sinais de campo."
    else:
        primary_alert = "Risco baixo no curto prazo para a area analisada."

    if territorial.get("vegetation_mismatch_flag"):
        recommended_action = "Priorizar vistoria de campo e investigacao de causa local nos talhoes afetados."
    elif risk_flags["dry_risk_flag"] and not agro_context["irrigated"]:
        recommended_action = "Priorizar monitoramento e irrigacao nos talhoes mais sensiveis."
    elif risk_flags["dry_risk_flag"] and agro_context["irrigated"]:
        recommended_action = "Revisar lamina e turno de irrigacao para mitigar estresse hidrico."
    elif risk_flags["heat_risk_flag"]:
        recommended_action = "Ajustar manejo e intensificar monitoramento em horarios de pico de calor."
    elif risk_flags["outside_zarc_flag"]:
        recommended_action = "Reavaliar janela de manejo e reforcar monitoramento por estar fora do ZARC."
    else:
        recommended_action = "Manter monitoramento de rotina e revisar analise a cada novo run de forecast."

    why_list = _build_why_list(risk_flags, climate_data, agro_context, climate_history=climate_history)
    culture = agro_context["culture_label"]

    copilot_response = {
        "summary": f"Esta area apresenta risco {risk_level} para a cultura {culture} no curto prazo.",
        "why": why_list,
        "action": recommended_action,
    }

    return {
        "primary_alert": primary_alert,
        "recommended_action": recommended_action,
        "copilot_response": copilot_response,
        "risk_score": risk_score,
    }
