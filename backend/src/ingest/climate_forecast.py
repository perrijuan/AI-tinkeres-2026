import hashlib
import math
import os
import random
from datetime import datetime, timedelta
from typing import Any

from src.ingest.gee_client import get_ee_client, to_ee_polygon
from src.utils.time import ensure_utc, latest_gfs_run_timestamp, to_iso_z


def _seed_from_context(lat: float, lon: float, analysis_timestamp: datetime) -> int:
    key = f"{lat:.4f}:{lon:.4f}:{analysis_timestamp.strftime('%Y%m%d%H')}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _round(value: float, digits: int = 1) -> float:
    return round(float(value), digits)


def _pick_band(available_bands: set[str], candidates: list[str]) -> str | None:
    for band in candidates:
        if band in available_bands:
            return band
    return None


def _to_celsius(temp_value: float) -> float:
    if temp_value > 170:
        return temp_value - 273.15
    return temp_value


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _region_mean(ee: Any, image: Any, geometry: Any, scale: int = 25_000) -> float | None:
    try:
        result = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=scale,
            bestEffort=True,
            maxPixels=1_000_000_000,
        ).getInfo()
        if not result:
            return None
        value = next(iter(result.values()))
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _try_get_gee_climate_forecast(
    spatial_context: dict[str, Any],
    analysis_timestamp: datetime,
    geometry: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if geometry is None:
        return None

    ee, gee_status = get_ee_client()
    if ee is None:
        return None

    try:
        analysis_utc = ensure_utc(analysis_timestamp)
        start_dt = analysis_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=15)

        polygon = to_ee_polygon(ee, geometry)
        centroid = ee.Geometry.Point([spatial_context["centroid_lon"], spatial_context["centroid_lat"]])

        collection = (
            ee.ImageCollection("NOAA/GFS0P25")
            .filterDate(to_iso_z(start_dt), to_iso_z(end_dt))
            .filterBounds(polygon)
            .sort("system:time_start")
        )

        if _safe_float(collection.size().getInfo()) == 0:
            return None

        first_image = ee.Image(collection.first())
        available_bands = set(first_image.bandNames().getInfo())

        precip_band = _pick_band(
            available_bands,
            [
                "total_precipitation_surface",
                "total_precipitation_surface_6_Hour_Accumulation",
                "precipitable_water_entire_atmosphere",
            ],
        )
        temp_band = _pick_band(available_bands, ["temperature_2m_above_ground"])
        humidity_band = _pick_band(available_bands, ["relative_humidity_2m_above_ground"])
        wind_band = _pick_band(available_bands, ["wind_speed_10m_above_ground"])
        u_wind_band = _pick_band(available_bands, ["u_component_of_wind_10m_above_ground"])
        v_wind_band = _pick_band(available_bands, ["v_component_of_wind_10m_above_ground"])

        if precip_band is None or temp_band is None:
            return None

        forecast_timeseries: list[dict[str, Any]] = []
        wind_values: list[float] = []

        for day in range(14):
            day_start = start_dt + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            day_collection = collection.filterDate(to_iso_z(day_start), to_iso_z(day_end))
            if _safe_float(day_collection.size().getInfo()) == 0:
                continue

            daily_precip_img = day_collection.select([precip_band]).sum()
            daily_temp_img = day_collection.select([temp_band]).mean()

            precip_mm = _region_mean(ee, daily_precip_img, centroid, scale=25_000)
            temp_raw = _region_mean(ee, daily_temp_img, centroid, scale=25_000)

            if precip_mm is None or temp_raw is None:
                continue

            humidity_pct = 65.0
            if humidity_band:
                hum_val = _region_mean(ee, day_collection.select([humidity_band]).mean(), centroid, scale=25_000)
                if hum_val is not None:
                    humidity_pct = max(0.0, min(100.0, hum_val))

            wind_ms = 3.0
            if wind_band:
                wind_val = _region_mean(ee, day_collection.select([wind_band]).mean(), centroid, scale=25_000)
                if wind_val is not None:
                    wind_ms = max(0.0, wind_val)
            elif u_wind_band and v_wind_band:
                u_val = _region_mean(ee, day_collection.select([u_wind_band]).mean(), centroid, scale=25_000)
                v_val = _region_mean(ee, day_collection.select([v_wind_band]).mean(), centroid, scale=25_000)
                if u_val is not None and v_val is not None:
                    wind_ms = max(0.0, math.sqrt(u_val**2 + v_val**2))

            wind_values.append(wind_ms)
            forecast_timeseries.append(
                {
                    "forecast_time": to_iso_z(day_start),
                    "precip_mm": _round(max(0.0, precip_mm), 1),
                    "temp_c": _round(_to_celsius(temp_raw), 1),
                    "humidity_pct": _round(humidity_pct, 1),
                }
            )

        if len(forecast_timeseries) < 7:
            return None

        first_7d = forecast_timeseries[:7]
        all_14d = forecast_timeseries[:14]
        precip_forecast_7d_mm = _round(sum(point["precip_mm"] for point in first_7d), 1)
        precip_forecast_14d_mm = _round(sum(point["precip_mm"] for point in all_14d), 1)
        temp_mean_7d_c = _round(sum(point["temp_c"] for point in first_7d) / len(first_7d), 1)
        temp_max_7d_c = _round(max(point["temp_c"] for point in first_7d), 1)
        humidity_mean_7d_pct = _round(sum(point["humidity_pct"] for point in first_7d) / len(first_7d), 1)
        wind_mean_7d_ms = _round(sum(wind_values[:7]) / max(1, len(wind_values[:7])), 1)

        return {
            "source": "gee",
            "provider": "Google Earth Engine",
            "model": "NOAA/GFS0P25",
            "gee_status": gee_status,
            "forecast_run_timestamp": to_iso_z(latest_gfs_run_timestamp(analysis_utc)),
            "precip_forecast_7d_mm": precip_forecast_7d_mm,
            "precip_forecast_14d_mm": precip_forecast_14d_mm,
            "temp_mean_7d_c": temp_mean_7d_c,
            "temp_max_7d_c": temp_max_7d_c,
            "humidity_mean_7d_pct": humidity_mean_7d_pct,
            "wind_mean_7d_ms": wind_mean_7d_ms,
            "forecast_timeseries": all_14d,
            "signals": [
                f"Precipitacao acumulada 7d: {precip_forecast_7d_mm} mm (GFS/GEE).",
                f"Temperatura maxima 7d: {temp_max_7d_c} C (GFS/GEE).",
                f"Umidade media 7d: {humidity_mean_7d_pct}% (GFS/GEE).",
            ],
        }
    except Exception:
        return None


def _get_synthetic_climate_forecast(spatial_context: dict[str, Any], analysis_timestamp: datetime) -> dict[str, Any]:
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
        "source": "synthetic",
        "provider": "SafraViva Synthetic Climate",
        "model": "deterministic_mvp_v1",
        "forecast_run_timestamp": to_iso_z(forecast_run),
        "precip_forecast_7d_mm": precip_forecast_7d_mm,
        "precip_forecast_14d_mm": precip_forecast_14d_mm,
        "temp_mean_7d_c": temp_mean_7d_c,
        "temp_max_7d_c": temp_max_7d_c,
        "humidity_mean_7d_pct": humidity_mean_7d_pct,
        "wind_mean_7d_ms": wind_mean_7d_ms,
        "forecast_timeseries": forecast_timeseries,
        "signals": [
            f"Precipitacao acumulada 7d: {precip_forecast_7d_mm} mm (fallback sintetico).",
            f"Temperatura maxima 7d: {temp_max_7d_c} C (fallback sintetico).",
            f"Umidade media 7d: {humidity_mean_7d_pct}% (fallback sintetico).",
        ],
    }


def get_climate_forecast(
    spatial_context: dict[str, Any],
    analysis_timestamp: datetime,
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    use_gee = os.environ.get("USE_GEE_CLIMATE", "true").strip().lower() not in {"0", "false", "no"}
    if use_gee:
        gee_data = _try_get_gee_climate_forecast(spatial_context, analysis_timestamp, geometry)
        if gee_data is not None:
            return gee_data
    return _get_synthetic_climate_forecast(spatial_context, analysis_timestamp)

