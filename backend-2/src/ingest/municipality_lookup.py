import json
from functools import lru_cache
from pathlib import Path
from typing import Any
import unicodedata

from src.utils.geo import compute_centroid, extract_outer_ring, haversine_km


def _default_geojson_paths() -> list[Path]:
    backend_root = Path(__file__).resolve().parents[2]
    repo_root = Path(__file__).resolve().parents[3]
    return [
        backend_root / "data" / "raw" / "municipios_mt.geojson",
        repo_root / "data" / "municipios_mt.geojson",
    ]


def _get_name(properties: dict[str, Any]) -> str:
    for key in properties.keys():
        normalized = unicodedata.normalize("NFKD", key).lower()
        lowered = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        if "munic" in lowered:
            return str(properties[key]).strip().title()
    return "Município não identificado"


def _get_uf(properties: dict[str, Any]) -> str:
    for key in properties.keys():
        lowered = key.lower()
        if lowered in {"uf", "estado"}:
            return str(properties[key]).strip().upper()
    return "MT"


def _feature_centroid(feature: dict[str, Any]) -> tuple[float, float] | None:
    geometry = feature.get("geometry", {})
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Point" and isinstance(coordinates, list) and len(coordinates) == 2:
        lon = float(coordinates[0])
        lat = float(coordinates[1])
        return lat, lon

    if geometry_type == "Polygon":
        try:
            ring = extract_outer_ring(geometry)
            return compute_centroid(ring)
        except ValueError:
            return None

    return None


@lru_cache(maxsize=1)
def _load_municipality_points() -> list[dict[str, Any]]:
    for path in _default_geojson_paths():
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        features = payload.get("features", [])
        points = []
        for feature in features:
            properties = feature.get("properties", {})
            centroid = _feature_centroid(feature)
            if centroid is None:
                continue
            lat, lon = centroid
            points.append(
                {
                    "municipio": _get_name(properties),
                    "uf": _get_uf(properties),
                    "lat": lat,
                    "lon": lon,
                }
            )
        if points:
            return points
    return []


def resolve_municipality(lat: float, lon: float) -> tuple[str, str]:
    points = _load_municipality_points()
    if not points:
        return "Município não identificado", "MT"

    nearest = min(points, key=lambda item: haversine_km(lat, lon, item["lat"], item["lon"]))
    return nearest["municipio"], nearest["uf"]
