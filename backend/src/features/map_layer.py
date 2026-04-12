from typing import Any


RISK_COLORS = {
    "baixo": {"fill": "#22c55e", "stroke": "#166534"},
    "moderado": {"fill": "#f59e0b", "stroke": "#92400e"},
    "alto": {"fill": "#ef4444", "stroke": "#991b1b"},
    "crítico": {"fill": "#7f1d1d", "stroke": "#450a0a"},
}


def build_map_layer(inputs: dict[str, Any], risk_result: dict[str, Any]) -> dict[str, Any]:
    risk_level = risk_result["risk_level"]
    colors = RISK_COLORS.get(risk_level, RISK_COLORS["moderado"])
    flags = risk_result["risk_flags"]
    culture = str(inputs["culture"]).lower().strip()

    if flags["dry_risk_flag"]:
        reason = "precipitação baixa nos próximos 7 dias"
    elif flags["heat_risk_flag"]:
        reason = "temperatura acima do limiar da cultura"
    elif flags["outside_zarc_flag"]:
        reason = "plantio fora da janela preferencial do ZARC"
    else:
        reason = "condições dentro do intervalo esperado"

    tooltip_summary = f"Risco {risk_level} | {culture} | {reason}"

    return {
        "geometry": inputs["geometry"],
        "fill_color": colors["fill"],
        "stroke_color": colors["stroke"],
        "tooltip_summary": tooltip_summary,
    }

