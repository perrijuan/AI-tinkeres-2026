from typing import Any

from src.ingest.municipality_lookup import resolve_municipality
from src.utils.geo import compute_bbox, compute_centroid, extract_outer_ring, polygon_area_hectares


def derive_spatial_context(inputs: dict[str, Any]) -> dict[str, Any]:
    geometry = inputs["geometry"]
    ring = extract_outer_ring(geometry)

    centroid_lat, centroid_lon = compute_centroid(ring)
    bbox = compute_bbox(ring)
    area_ha = polygon_area_hectares(ring)
    municipio, uf = resolve_municipality(centroid_lat, centroid_lon)

    return {
        "centroid_lat": round(centroid_lat, 6),
        "centroid_lon": round(centroid_lon, 6),
        "bbox_min_lat": round(bbox["bbox_min_lat"], 6),
        "bbox_max_lat": round(bbox["bbox_max_lat"], 6),
        "bbox_min_lon": round(bbox["bbox_min_lon"], 6),
        "bbox_max_lon": round(bbox["bbox_max_lon"], 6),
        "area_ha": area_ha,
        "municipio": municipio,
        "uf": uf,
    }

