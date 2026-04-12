import hashlib
import math
import random
from datetime import datetime, timedelta
from typing import Any

from src.utils.time import ensure_utc, latest_gfs_run_timestamp, to_iso_z


def _seed_from_context(lat: float, lon: float, analysis_timestamp: datetime) -> int:
    key = f"{lat:.4f}:{lon:.4f}:{analysis_timestamp.strftime('%Y%m%d%H')}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _round(value: float, digits: int = 1) -> float:
    return round(float(value), digits)


def get_climate_forecast(spatial_context: dict[str, Any], analysis_timestamp: datetime) -> dict[str, Any]:
    centroid_lat = float(spatial_context["centroid_lat"])
    centroid_lon = float(spatial_context["centroid_lon"])
    analysis_utc = ensure_utc(analysis_timestamp)
    forecast_run = latest_gfs_run_timestamp(analysis_utc)

    rng = random.Random(_seed_from_context(centroid_lat, centroid_lon, analysis_utc))
    day0 = analysis_utc.replace(hour=0, minute=0, second=0, microsecond=0)

    forecast_timeseries: list[dict[str, Any]] = []
    wind_values: list[float] = []

    for step in range(14):
        current_ts = day0 + timedelta(days=step)
        year_progress = (current_ts.timetuple().tm_yday / 365.0) * 2 * math.pi
        seasonal = math.sin(year_progress)
        regional_bias = 0.9 + 0.1 * math.sin(math.radians(abs(centroid_lon) * 3))

        precip = max(0.0, (4.4 + 1.8 * seasonal) * regional_bias + rng.uniform(-2.8, 2.6))
        temp = 25.5 + 0.22 * abs(centroid_lat + 15) + (1.7 - seasonal) + rng.uniform(-1.4, 1.4)
        humidity = 56 + precip * 3.8 - max(0.0, temp - 31.0) * 2.6 + rng.uniform(-5.0, 5.0)
        humidity = max(25.0, min(98.0, humidity))
        wind = 2.4 + max(0.0, temp - 30.0) * 0.18 + rng.uniform(0.3, 2.8)
        wind_values.append(wind)

        forecast_timeseries.append(
            {
                "forecast_time": to_iso_z(current_ts),
                "precip_mm": _round(precip),
                "temp_c": _round(temp),
                "humidity_pct": _round(humidity),
            }
        )

    first_7d = forecast_timeseries[:7]
    all_14d = forecast_timeseries

    precip_forecast_7d_mm = _round(sum(point["precip_mm"] for point in first_7d), 1)
    precip_forecast_14d_mm = _round(sum(point["precip_mm"] for point in all_14d), 1)
    temp_mean_7d_c = _round(sum(point["temp_c"] for point in first_7d) / len(first_7d), 1)
    temp_max_7d_c = _round(max(point["temp_c"] for point in first_7d), 1)
    humidity_mean_7d_pct = _round(sum(point["humidity_pct"] for point in first_7d) / len(first_7d), 1)
    wind_mean_7d_ms = _round(sum(wind_values[:7]) / 7.0, 1)

    return {
        "forecast_run_timestamp": to_iso_z(forecast_run),
        "precip_forecast_7d_mm": precip_forecast_7d_mm,
        "precip_forecast_14d_mm": precip_forecast_14d_mm,
        "temp_mean_7d_c": temp_mean_7d_c,
        "temp_max_7d_c": temp_max_7d_c,
        "humidity_mean_7d_pct": humidity_mean_7d_pct,
        "wind_mean_7d_ms": wind_mean_7d_ms,
        "forecast_timeseries": forecast_timeseries,
    }

