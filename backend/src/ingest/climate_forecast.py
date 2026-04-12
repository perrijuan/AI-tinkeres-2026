import hashlib
import math
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from src.ingest.gee_client import get_ee_client, to_ee_polygon
from src.utils.time import ensure_utc, latest_gfs_run_timestamp, to_iso_z


def _seed_from_context(lat: float, lon: float, analysis_timestamp: datetime) -> int:
    key = f"{lat:.4f}:{lon:.4f}:{analysis_timestamp.strftime('%Y%m%d%H')}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _round(value: float, digits: int = 1) -> float:
    return round(float(value), digits)


def _to_celsius(temp_value: float) -> float:
    if temp_value > 170:
        return temp_value - 273.15
    return temp_value


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_epoch_millis(value: datetime) -> int:
    return int(ensure_utc(value).timestamp() * 1000)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
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
        # Daily series should represent "next days" from the day after analysis.
        start_dt = analysis_utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end_dt = start_dt + timedelta(days=14)
        polygon = to_ee_polygon(ee, geometry)
        centroid = ee.Geometry.Point([spatial_context["centroid_lon"], spatial_context["centroid_lat"]])
        analysis_ms = _to_epoch_millis(analysis_utc)

        # Use a short lookback window to keep queries fast, with safe fallback to full history.
        recent_window_ms = _to_epoch_millis(analysis_utc - timedelta(days=3))
        base_collection = (
            ee.ImageCollection("NOAA/GFS0P25")
            .filterBounds(polygon)
            .filter(ee.Filter.gte("creation_time", recent_window_ms))
            .filter(ee.Filter.lte("creation_time", analysis_ms))
        )
        latest_run_ms = int(_safe_float(base_collection.aggregate_max("creation_time").getInfo()))
        if latest_run_ms <= 0:
            base_collection = (
                ee.ImageCollection("NOAA/GFS0P25")
                .filterBounds(polygon)
                .filter(ee.Filter.lte("creation_time", analysis_ms))
            )
            latest_run_ms = int(_safe_float(base_collection.aggregate_max("creation_time").getInfo()))
        if latest_run_ms <= 0:
            return None

        run_collection = (
            base_collection.filter(ee.Filter.eq("creation_time", latest_run_ms))
            .filter(ee.Filter.gte("forecast_time", _to_epoch_millis(start_dt)))
            .filter(ee.Filter.lt("forecast_time", _to_epoch_millis(end_dt)))
            .sort("forecast_time")
        )

        def _sample_image(image: Any) -> Any:
            reduced = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=centroid,
                scale=25_000,
                bestEffort=True,
                maxPixels=1_000_000_000,
            )
            return ee.Feature(None, reduced).set(
                {
                    "forecast_time": image.get("forecast_time"),
                    "forecast_hours": image.get("forecast_hours"),
                }
            )

        sampled_features = ee.FeatureCollection(run_collection.map(_sample_image)).getInfo().get("features", [])
        if not sampled_features:
            return None

        records: list[dict[str, Any]] = []
        for feature in sampled_features:
            props = feature.get("properties", {})
            forecast_time_ms = _optional_float(props.get("forecast_time"))
            forecast_hours = _optional_float(props.get("forecast_hours"))
            if forecast_time_ms is None or forecast_hours is None:
                continue

            records.append(
                {
                    "forecast_time_ms": forecast_time_ms,
                    "forecast_hours": forecast_hours,
                    "temp_raw": _optional_float(props.get("temperature_2m_above_ground")),
                    "humidity_raw": _optional_float(props.get("relative_humidity_2m_above_ground")),
                    "precip_total_raw": _optional_float(props.get("total_precipitation_surface")),
                    "precip_rate_raw": _optional_float(props.get("precipitation_rate")),
                    "wind_speed_raw": _optional_float(props.get("wind_speed_10m_above_ground")),
                    "u_wind_raw": _optional_float(props.get("u_component_of_wind_10m_above_ground")),
                    "v_wind_raw": _optional_float(props.get("v_component_of_wind_10m_above_ground")),
                }
            )

        if not records:
            return None

        records.sort(key=lambda item: item["forecast_hours"])
        for index, record in enumerate(records):
            if index == 0:
                record["step_hours"] = max(1.0, record["forecast_hours"])
            else:
                delta = record["forecast_hours"] - records[index - 1]["forecast_hours"]
                record["step_hours"] = max(1.0, delta)

        daily: dict[str, dict[str, list[float]]] = {}
        for record in records:
            forecast_dt = datetime.fromtimestamp(record["forecast_time_ms"] / 1000, tz=timezone.utc)
            if forecast_dt < start_dt or forecast_dt >= end_dt:
                continue

            day_key = forecast_dt.strftime("%Y-%m-%d")
            bucket = daily.setdefault(
                day_key,
                {"precip": [], "temp": [], "humidity": [], "wind": []},
            )

            temp_raw = record["temp_raw"]
            if temp_raw is not None:
                bucket["temp"].append(_to_celsius(temp_raw))

            humidity_raw = record["humidity_raw"]
            if humidity_raw is not None:
                bucket["humidity"].append(max(0.0, min(100.0, humidity_raw)))

            wind_speed = record["wind_speed_raw"]
            if wind_speed is None and record["u_wind_raw"] is not None and record["v_wind_raw"] is not None:
                wind_speed = math.sqrt(record["u_wind_raw"] ** 2 + record["v_wind_raw"] ** 2)
            if wind_speed is not None:
                bucket["wind"].append(max(0.0, wind_speed))

            precip_total = record["precip_total_raw"]
            if precip_total is not None:
                bucket["precip"].append(max(0.0, precip_total))
            elif record["precip_rate_raw"] is not None:
                step_seconds = record["step_hours"] * 3600.0
                bucket["precip"].append(max(0.0, record["precip_rate_raw"] * step_seconds))

        forecast_timeseries: list[dict[str, Any]] = []
        wind_values: list[float] = []
        for day in range(14):
            day_dt = start_dt + timedelta(days=day)
            day_key = day_dt.strftime("%Y-%m-%d")
            bucket = daily.get(day_key)
            if not bucket or not bucket["temp"]:
                continue

            precip_mm = sum(bucket["precip"]) if bucket["precip"] else 0.0
            temp_c = sum(bucket["temp"]) / len(bucket["temp"])
            humidity_pct = (sum(bucket["humidity"]) / len(bucket["humidity"])) if bucket["humidity"] else 65.0
            wind_ms = (sum(bucket["wind"]) / len(bucket["wind"])) if bucket["wind"] else 3.0

            wind_values.append(wind_ms)
            forecast_timeseries.append(
                {
                    "forecast_time": to_iso_z(day_dt),
                    "precip_mm": _round(precip_mm, 1),
                    "temp_c": _round(temp_c, 1),
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
        run_ts_iso = datetime.fromtimestamp(latest_run_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "source": "gee",
            "provider": "Google Earth Engine",
            "model": "NOAA/GFS0P25",
            "gee_status": gee_status,
            "forecast_run_timestamp": run_ts_iso,
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
