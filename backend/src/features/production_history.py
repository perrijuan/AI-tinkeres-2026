import csv
import hashlib
import math
import unicodedata
from functools import lru_cache
from pathlib import Path
from statistics import pstdev
from typing import Any


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _hash_ratio(seed_text: str) -> float:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    raw = str(value).strip()
    if raw in {"", "..", "-"}:
        return None
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        parsed = float(raw)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _to_int(value: Any) -> int | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _coefficient_of_variation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_value = _safe_mean(values)
    if mean_value <= 0:
        return 0.0
    return float(pstdev(values) / mean_value)


def _trend_label(first: float, last: float, stable_band: float = 0.03) -> str:
    if first <= 0:
        return "estavel"
    delta = (last - first) / first
    if delta > stable_band:
        return "alta"
    if delta < -stable_band:
        return "queda"
    return "estavel"


def _resolve_metric_bucket(metric_name_norm: str) -> str | None:
    if "area plantada" in metric_name_norm:
        return "area_planted_ha"
    if "area colhida" in metric_name_norm:
        return "area_harvested_ha"
    if "quantidade produzida" in metric_name_norm:
        return "production_tons"
    if "rendimento medio" in metric_name_norm:
        return "yield_kg_ha"
    if "valor da producao" in metric_name_norm:
        return "value_mil_reais"
    return None


def _dataset_paths() -> list[Path]:
    backend_root = Path(__file__).resolve().parents[2]
    return [
        backend_root / "dataset" / "extracao_mt_5_anos.csv",
        backend_root / "dataset" / "extracao_mt_5anos.csv",
    ]


@lru_cache(maxsize=1)
def _load_history_series() -> list[dict[str, Any]]:
    for path in _dataset_paths():
        if not path.exists():
            continue

        for encoding in ["utf-8-sig", "latin-1"]:
            try:
                yearly: dict[int, dict[str, float | int]] = {}
                with path.open("r", encoding=encoding, newline="") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        uf_name = _normalize_text(row.get("D1N"))
                        if uf_name != "mato grosso":
                            continue

                        year = _to_int(row.get("D2N") or row.get("D2C"))
                        metric_name_norm = _normalize_text(row.get("D3N"))
                        metric_bucket = _resolve_metric_bucket(metric_name_norm)
                        value = _to_float(row.get("V"))

                        if year is None or metric_bucket is None:
                            continue

                        current = yearly.setdefault(year, {"year": year})
                        if value is not None:
                            current[metric_bucket] = value

                if yearly:
                    return [yearly[year] for year in sorted(yearly.keys())]
            except Exception:
                continue
    return []


def _fallback_context(culture: str, municipio: str, uf: str) -> dict[str, Any]:
    seed = f"{uf}:{municipio}:{culture}"
    volatility = round(0.08 + (_hash_ratio(seed + ":volatility") * 0.18), 3)
    mean_index = round(0.85 + (_hash_ratio(seed + ":mean") * 0.35), 3)
    trend_selector = _hash_ratio(seed + ":trend")
    if trend_selector < 0.33:
        trend = "queda"
    elif trend_selector < 0.66:
        trend = "estavel"
    else:
        trend = "alta"

    return {
        "provider": "IBGE/PAM (fallback heuristico)",
        "source": "heuristic",
        "scope": "municipio/cultura sintetico",
        "period_start": None,
        "period_end": None,
        "yield_mean_index": mean_index,
        "yield_volatility": volatility,
        "yield_trend": trend,
        "signals": [
            "Historico de producao nao encontrado no dataset local.",
            "Aplicado contexto historico heuristico para manter o score operacional.",
        ],
    }


def get_historical_yield_context(culture: str, municipio: str, uf: str = "MT") -> dict[str, Any]:
    history_rows = _load_history_series()
    if not history_rows:
        return _fallback_context(culture=culture, municipio=municipio, uf=uf)

    years = [int(row["year"]) for row in history_rows]

    area_series = [float(row["area_harvested_ha"]) for row in history_rows if row.get("area_harvested_ha") is not None]
    value_per_ha_series: list[float] = []
    for row in history_rows:
        area_harvested = row.get("area_harvested_ha")
        value_mil_reais = row.get("value_mil_reais")
        if area_harvested is None or value_mil_reais is None:
            continue
        if float(area_harvested) <= 0:
            continue
        value_per_ha_series.append((float(value_mil_reais) * 1000.0) / float(area_harvested))

    if len(value_per_ha_series) >= 3:
        proxy_series = value_per_ha_series
        proxy_label = "valor por hectare (R$/ha)"
    elif len(area_series) >= 3:
        proxy_series = area_series
        proxy_label = "area colhida (ha)"
    else:
        return _fallback_context(culture=culture, municipio=municipio, uf=uf)

    proxy_mean = _safe_mean(proxy_series)
    latest_proxy = proxy_series[-1]
    volatility = round(max(0.0, _coefficient_of_variation(proxy_series)), 3)
    yield_mean_index = round(max(0.4, min(1.8, latest_proxy / max(proxy_mean, 1e-6))), 3)
    trend = _trend_label(proxy_series[0], latest_proxy)

    signals = [
        "Historico de producao integrado de extracao_mt_5_anos.csv.",
        f"Serie usada para contexto de produtividade: {proxy_label}.",
        f"Janela historica carregada: {years[0]}-{years[-1]} (UF MT, agregado).",
    ]
    if value_per_ha_series:
        signals.append(f"Valor por hectare no ultimo ano: {round(value_per_ha_series[-1], 2)} R$/ha.")

    return {
        "provider": "IBGE/PAM (dataset local)",
        "source": "dataset",
        "scope": "UF MT agregado (sem recorte municipal/cultura no arquivo atual)",
        "period_start": years[0],
        "period_end": years[-1],
        "yield_mean_index": yield_mean_index,
        "yield_volatility": volatility,
        "yield_trend": trend,
        "years": years,
        "value_per_ha_series": [round(value, 2) for value in value_per_ha_series],
        "signals": signals,
    }
