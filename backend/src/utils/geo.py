import math
from typing import Iterable


Coordinate = tuple[float, float]


def ensure_closed_ring(coordinates: Iterable[Coordinate]) -> list[Coordinate]:
    ring = list(coordinates)
    if len(ring) < 3:
        raise ValueError("Polygon precisa ter pelo menos 3 vértices.")
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    if len(ring) < 4:
        raise ValueError("Anel do polígono inválido.")
    return ring


def extract_outer_ring(geometry: dict) -> list[Coordinate]:
    if geometry.get("type") != "Polygon":
        raise ValueError("A geometria deve ser do tipo Polygon.")
    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or not rings:
        raise ValueError("Polygon sem coordenadas.")

    outer = rings[0]
    parsed: list[Coordinate] = []
    for point in outer:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("Cada coordenada deve ter [lon, lat].")
        lon = float(point[0])
        lat = float(point[1])
        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"Longitude inválida: {lon}")
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"Latitude inválida: {lat}")
        parsed.append((lon, lat))

    return ensure_closed_ring(parsed)


def compute_centroid(ring: list[Coordinate]) -> tuple[float, float]:
    signed_area_x2 = 0.0
    centroid_lon_acc = 0.0
    centroid_lat_acc = 0.0

    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        cross = (x1 * y2) - (x2 * y1)
        signed_area_x2 += cross
        centroid_lon_acc += (x1 + x2) * cross
        centroid_lat_acc += (y1 + y2) * cross

    if abs(signed_area_x2) < 1e-12:
        avg_lon = sum(lon for lon, _ in ring[:-1]) / (len(ring) - 1)
        avg_lat = sum(lat for _, lat in ring[:-1]) / (len(ring) - 1)
        return avg_lat, avg_lon

    centroid_lon = centroid_lon_acc / (3.0 * signed_area_x2)
    centroid_lat = centroid_lat_acc / (3.0 * signed_area_x2)
    return centroid_lat, centroid_lon


def compute_bbox(ring: list[Coordinate]) -> dict[str, float]:
    lons = [lon for lon, _ in ring]
    lats = [lat for _, lat in ring]
    return {
        "bbox_min_lat": min(lats),
        "bbox_max_lat": max(lats),
        "bbox_min_lon": min(lons),
        "bbox_max_lon": max(lons),
    }


def polygon_area_hectares(ring: list[Coordinate]) -> float:
    earth_radius_m = 6_371_008.8
    area_component = 0.0

    for i in range(len(ring) - 1):
        lon1, lat1 = ring[i]
        lon2, lat2 = ring[i + 1]
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        area_component += (lon2_rad - lon1_rad) * (2 + math.sin(lat1_rad) + math.sin(lat2_rad))

    area_m2 = abs(area_component) * (earth_radius_m**2) / 2.0
    area_ha = area_m2 / 10_000.0
    return round(area_ha, 2)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6_371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(a))

