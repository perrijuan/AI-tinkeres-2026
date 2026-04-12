import csv
import math
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace(",", ".")
    try:
        return float(normalized)
    except Exception:
        return None


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _find_col_index(header: list[str], contains_text: str) -> int | None:
    normalized_target = _normalize_text(contains_text)
    for idx, col in enumerate(header):
        if normalized_target in _normalize_text(col):
            return idx
    return None


def _coord_from_dms(deg: Any, minutes: Any, seconds: Any, hemisphere: Any) -> float | None:
    deg_f = _to_float(deg)
    min_f = _to_float(minutes)
    sec_f = _to_float(seconds)
    if deg_f is None or min_f is None or sec_f is None:
        return None
    decimal = abs(deg_f) + (min_f / 60.0) + (sec_f / 3600.0)
    hemi = _normalize_text(str(hemisphere or ""))
    if hemi.startswith("s") or hemi.startswith("o") or hemi.startswith("w"):
        decimal = -decimal
    return decimal


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(d_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(1e-12, 1.0 - a)))
    return radius_km * c


def _soil_quality_index(ph_h2o: float | None, base_saturation_pct: float | None, organic_carbon: float | None) -> float:
    parts: list[tuple[float, float]] = []
    if ph_h2o is not None:
        ph_score = _clamp(1.0 - abs(ph_h2o - 6.0) / 2.0, 0.0, 1.0)
        parts.append((0.45, ph_score))
    if base_saturation_pct is not None:
        v_score = _clamp((base_saturation_pct - 20.0) / 60.0, 0.0, 1.0)
        parts.append((0.35, v_score))
    if organic_carbon is not None:
        carbon_score = _clamp(organic_carbon / 20.0, 0.0, 1.0)
        parts.append((0.20, carbon_score))
    if not parts:
        return 0.50
    weight_sum = sum(weight for weight, _ in parts)
    return _clamp(sum(weight * score for weight, score in parts) / weight_sum, 0.0, 1.0)


def _soil_label(index: float) -> str:
    if index >= 0.70:
        return "boa"
    if index >= 0.50:
        return "media"
    return "baixa"


@lru_cache(maxsize=1)
def _load_soil_samples() -> list[dict[str, Any]]:
    backend_root = Path(__file__).resolve().parents[2]
    path = backend_root / "dataset" / "parametros_do_solo.csv"
    if not path.exists():
        return []

    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                rows = list(csv.reader(file, delimiter=";", quotechar='"'))
            break
        except UnicodeDecodeError:
            continue
    else:
        return []

    if len(rows) < 4:
        return []

    header = rows[2]
    municipality_idx = _find_col_index(header, "municipio")
    uf_idx = _find_col_index(header, "uf")
    lat_deg_idx = _find_col_index(header, "latitude graus")
    lat_min_idx = _find_col_index(header, "latitude minutos")
    lat_sec_idx = _find_col_index(header, "latitude segundos")
    lat_hemi_idx = _find_col_index(header, "latitude hemisf")
    lon_deg_idx = _find_col_index(header, "longitude graus")
    lon_min_idx = _find_col_index(header, "longitude minutos")
    lon_sec_idx = _find_col_index(header, "longitude segundos")
    lon_hemi_idx = _find_col_index(header, "longitude hemisf")
    ph_idx = _find_col_index(header, "ph - h2o")
    base_sat_idx = _find_col_index(header, "valor v")
    carbon_idx = _find_col_index(header, "carbono organico")

    required = [
        municipality_idx,
        uf_idx,
        lat_deg_idx,
        lat_min_idx,
        lat_sec_idx,
        lat_hemi_idx,
        lon_deg_idx,
        lon_min_idx,
        lon_sec_idx,
        lon_hemi_idx,
    ]
    if any(idx is None for idx in required):
        return []

    samples: list[dict[str, Any]] = []
    for row in rows[3:]:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))

        uf = row[uf_idx].strip().upper() if uf_idx is not None else ""
        if uf and uf != "MT":
            continue

        municipio = row[municipality_idx].strip() if municipality_idx is not None else ""
        if not municipio:
            continue

        lat = _coord_from_dms(
            row[lat_deg_idx],
            row[lat_min_idx],
            row[lat_sec_idx],
            row[lat_hemi_idx],
        )
        lon = _coord_from_dms(
            row[lon_deg_idx],
            row[lon_min_idx],
            row[lon_sec_idx],
            row[lon_hemi_idx],
        )
        if lat is None or lon is None:
            continue

        ph_h2o = _to_float(row[ph_idx]) if ph_idx is not None else None
        base_saturation_pct = _to_float(row[base_sat_idx]) if base_sat_idx is not None else None
        organic_carbon = _to_float(row[carbon_idx]) if carbon_idx is not None else None
        soil_index = round(_soil_quality_index(ph_h2o, base_saturation_pct, organic_carbon), 3)

        samples.append(
            {
                "uf": uf or "MT",
                "municipio": municipio,
                "municipio_norm": _normalize_text(municipio),
                "lat": lat,
                "lon": lon,
                "ph_h2o": ph_h2o,
                "base_saturation_pct": base_saturation_pct,
                "organic_carbon": organic_carbon,
                "soil_quality_index": soil_index,
            }
        )

    return samples


def get_soil_context(spatial_context: dict[str, Any]) -> dict[str, Any]:
    samples = _load_soil_samples()
    if not samples:
        return {
            "source": "fallback",
            "provider": "BDSolos/Embrapa",
            "interpretation_scope": "estrutural",
            "temporal_nature": "historico_heterogeneo",
            "short_term_reliability": "baixa",
            "soil_quality_index": 0.50,
            "soil_quality_label": "media",
            "soil_good_flag": False,
            "confidence_index": 0.30,
            "sample_count": 0,
            "nearest_sample_km": None,
            "signals": [
                "Base de solo indisponivel. Usando indice neutro de solo.",
                "Solo deve ser interpretado como contexto estrutural, nao como diagnostico dinamico da safra atual.",
            ],
        }

    centroid_lat = float(spatial_context["centroid_lat"])
    centroid_lon = float(spatial_context["centroid_lon"])
    municipio_norm = _normalize_text(spatial_context["municipio"])
    municipality_samples = [s for s in samples if s["municipio_norm"] == municipio_norm]
    candidates = municipality_samples or samples

    nearest = min(candidates, key=lambda sample: _distance_km(centroid_lat, centroid_lon, sample["lat"], sample["lon"]))
    nearest_distance_km = round(_distance_km(centroid_lat, centroid_lon, nearest["lat"], nearest["lon"]), 2)

    if municipality_samples:
        municipal_avg = sum(s["soil_quality_index"] for s in municipality_samples) / len(municipality_samples)
        soil_quality_index = round((nearest["soil_quality_index"] * 0.65) + (municipal_avg * 0.35), 3)
    else:
        soil_quality_index = nearest["soil_quality_index"]

    soil_quality_label = _soil_label(soil_quality_index)
    soil_good_flag = soil_quality_index >= 0.62
    sample_density_score = _clamp(len(candidates) / 25.0, 0.0, 1.0)
    distance_score = _clamp(1.0 - (nearest_distance_km / 80.0), 0.0, 1.0)
    confidence_index = round((0.55 * sample_density_score) + (0.45 * distance_score), 3)

    signals: list[str] = [
        f"Qualidade de solo estimada: {soil_quality_index} ({soil_quality_label}).",
        f"Amostras locais consideradas: {len(candidates)}.",
        f"Distancia da amostra de referencia: {nearest_distance_km} km.",
        "Dados de solo sao historicos e heterogeneos no tempo; uso recomendado como contexto estrutural.",
    ]
    if nearest.get("ph_h2o") is not None:
        signals.append(f"pH H2O da amostra de referencia: {round(float(nearest['ph_h2o']), 2)}.")
    if nearest.get("base_saturation_pct") is not None:
        signals.append(f"Saturacao por bases (V%): {round(float(nearest['base_saturation_pct']), 1)}.")

    return {
        "source": "dataset",
        "provider": "BDSolos/Embrapa (dataset local)",
        "interpretation_scope": "estrutural",
        "temporal_nature": "historico_heterogeneo",
        "short_term_reliability": "baixa",
        "soil_quality_index": soil_quality_index,
        "soil_quality_label": soil_quality_label,
        "soil_good_flag": soil_good_flag,
        "confidence_index": confidence_index,
        "sample_count": len(candidates),
        "nearest_sample_km": nearest_distance_km,
        "signals": signals,
    }
