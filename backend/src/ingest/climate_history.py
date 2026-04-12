import hashlib
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from src.ingest.gee_client import get_ee_client, to_ee_polygon
from src.utils.time import ensure_utc, to_iso_z


def _round(value: float, digits: int = 1) -> float:
    return round(float(value), digits)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _optional_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _seed_from_context(lat: float, lon: float, analysis_timestamp: datetime) -> int:
    key = f"{lat:.4f}:{lon:.4f}:{analysis_timestamp.strftime('%Y%m%d')}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _shift_year_safe(value: datetime, years_back: int) -> datetime:
    target_year = value.year - years_back
    try:
        return value.replace(year=target_year)
    except ValueError:
        # Handle leap year day.
        return value.replace(month=2, day=28, year=target_year)


def _to_epoch_millis(value: datetime) -> int:
    return int(ensure_utc(value).timestamp() * 1000)


def _sum_precip_mm(ee: Any, collection: Any, geometry: Any, scale: int = 5_000) -> float | None:
    try:
        summed = collection.select(["precipitation"]).sum()
        values = summed.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=scale,
            bestEffort=True,
            maxPixels=1_000_000_000,
        ).getInfo()
        if not values:
            return None
        value = values.get("precipitation")
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _try_get_gee_chirps_history(
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
        analysis_day = analysis_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        polygon = to_ee_polygon(ee, geometry)
        centroid = ee.Geometry.Point([spatial_context["centroid_lon"], spatial_context["centroid_lat"]])

        base_collection = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(polygon)
        if _safe_float(base_collection.size().getInfo()) == 0:
            return None

        latest_ms = int(_safe_float(base_collection.aggregate_max("system:time_start").getInfo()))
        if latest_ms <= 0:
            return None

        latest_day_start = datetime.fromtimestamp(latest_ms / 1000.0, tz=timezone.utc)
        latest_day_end = latest_day_start + timedelta(days=1)
        end_dt = min(analysis_day + timedelta(days=1), latest_day_end)
        data_lag_days = max(0, (analysis_day - latest_day_start).days)

        start_30d = end_dt - timedelta(days=30)
        start_7d = end_dt - timedelta(days=7)

        collection_30d = base_collection.filterDate(to_iso_z(start_30d), to_iso_z(end_dt)).sort("system:time_start")
        collection_7d = base_collection.filterDate(to_iso_z(start_7d), to_iso_z(end_dt)).sort("system:time_start")

        if _safe_float(collection_30d.size().getInfo()) == 0:
            return None

        precip_observed_7d_mm = _sum_precip_mm(ee, collection_7d, centroid)
        precip_observed_30d_mm = _sum_precip_mm(ee, collection_30d, centroid)
        if precip_observed_7d_mm is None or precip_observed_30d_mm is None:
            return None

        daily_rows = (
            collection_30d.select(["precipitation"])
            .getRegion(centroid, 5_000)
            .getInfo()
        )
        if not daily_rows or len(daily_rows) < 2:
            return None

        header = daily_rows[0]
        time_idx = header.index("time")
        precip_idx = header.index("precipitation")
        timeseries_30d: list[dict[str, Any]] = []
        for row in daily_rows[1:]:
            if not row or len(row) <= max(time_idx, precip_idx):
                continue
            ts_ms = _optional_float(row[time_idx])
            precip_val = _optional_float(row[precip_idx])
            if ts_ms is None or precip_val is None:
                continue
            date_str = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).date().isoformat()
            timeseries_30d.append({"date": date_str, "precip_mm": _round(max(0.0, precip_val), 1)})

        timeseries_30d.sort(key=lambda item: item["date"])
        if len(timeseries_30d) > 30:
            timeseries_30d = timeseries_30d[-30:]

        dry_days_30d = sum(1 for point in timeseries_30d if point["precip_mm"] < 1.0)

        climatology_values: list[float] = []
        for years_back in range(1, 6):
            hist_start = _shift_year_safe(start_30d, years_back)
            hist_end = _shift_year_safe(end_dt, years_back)
            hist_collection = base_collection.filterDate(to_iso_z(hist_start), to_iso_z(hist_end))
            if _safe_float(hist_collection.size().getInfo()) == 0:
                continue
            hist_sum = _sum_precip_mm(ee, hist_collection, centroid)
            if hist_sum is None:
                continue
            climatology_values.append(hist_sum)

        precip_climatology_30d_mm = None
        precip_anomaly_30d_mm = None
        precip_anomaly_30d_pct = None
        if climatology_values:
            precip_climatology_30d_mm = sum(climatology_values) / len(climatology_values)
            precip_anomaly_30d_mm = precip_observed_30d_mm - precip_climatology_30d_mm
            if precip_climatology_30d_mm > 0:
                precip_anomaly_30d_pct = (precip_anomaly_30d_mm / precip_climatology_30d_mm) * 100.0

        signals = [
            f"CHIRPS observado 7d: {_round(precip_observed_7d_mm)} mm.",
            f"CHIRPS observado 30d: {_round(precip_observed_30d_mm)} mm.",
            f"Dias secos (<1mm) em 30d: {dry_days_30d}.",
            f"Ultimo dado CHIRPS disponivel em {latest_day_start.date().isoformat()} (defasagem: {data_lag_days} dias).",
        ]
        if precip_anomaly_30d_pct is not None:
            signals.append(f"Anomalia de precipitacao 30d: {_round(precip_anomaly_30d_pct, 1)}%.")

        return {
            "source": "gee",
            "provider": "Google Earth Engine",
            "dataset": "UCSB-CHG/CHIRPS/DAILY",
            "gee_status": gee_status,
            "window_start": to_iso_z(start_30d),
            "window_end": to_iso_z(end_dt),
            "latest_observed_date": latest_day_start.date().isoformat(),
            "data_lag_days": int(data_lag_days),
            "precip_observed_7d_mm": _round(precip_observed_7d_mm, 1),
            "precip_observed_30d_mm": _round(precip_observed_30d_mm, 1),
            "precip_climatology_30d_mm": _round(precip_climatology_30d_mm, 1) if precip_climatology_30d_mm is not None else None,
            "precip_anomaly_30d_mm": _round(precip_anomaly_30d_mm, 1) if precip_anomaly_30d_mm is not None else None,
            "precip_anomaly_30d_pct": _round(precip_anomaly_30d_pct, 1) if precip_anomaly_30d_pct is not None else None,
            "dry_days_30d": int(dry_days_30d),
            "timeseries_30d": timeseries_30d,
            "signals": signals,
        }
    except Exception:
        return None


def _get_synthetic_climate_history(spatial_context: dict[str, Any], analysis_timestamp: datetime) -> dict[str, Any]:
    centroid_lat = float(spatial_context["centroid_lat"])
    centroid_lon = float(spatial_context["centroid_lon"])
    analysis_utc = ensure_utc(analysis_timestamp)
    start_30d = analysis_utc.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=29)
    end_30d = start_30d + timedelta(days=30)

    rng = random.Random(_seed_from_context(centroid_lat, centroid_lon, analysis_utc))
    daily_values: list[float] = []
    timeseries_30d: list[dict[str, Any]] = []
    for step in range(30):
        current = start_30d + timedelta(days=step)
        precip_mm = max(0.0, 3.2 + rng.uniform(-2.5, 7.8))
        daily_values.append(precip_mm)
        timeseries_30d.append({"date": current.date().isoformat(), "precip_mm": _round(precip_mm, 1)})

    precip_observed_30d_mm = sum(daily_values)
    precip_observed_7d_mm = sum(daily_values[-7:])
    precip_climatology_30d_mm = precip_observed_30d_mm * (0.92 + rng.uniform(0.0, 0.22))
    precip_anomaly_30d_mm = precip_observed_30d_mm - precip_climatology_30d_mm
    precip_anomaly_30d_pct = (
        (precip_anomaly_30d_mm / precip_climatology_30d_mm) * 100.0
        if precip_climatology_30d_mm > 0
        else 0.0
    )
    dry_days_30d = sum(1 for value in daily_values if value < 1.0)

    return {
        "source": "synthetic",
        "provider": "SafraViva Synthetic Climate History",
        "dataset": "deterministic_mvp_v1",
        "window_start": to_iso_z(start_30d),
        "window_end": to_iso_z(end_30d),
        "latest_observed_date": (end_30d - timedelta(days=1)).date().isoformat(),
        "data_lag_days": 0,
        "precip_observed_7d_mm": _round(precip_observed_7d_mm, 1),
        "precip_observed_30d_mm": _round(precip_observed_30d_mm, 1),
        "precip_climatology_30d_mm": _round(precip_climatology_30d_mm, 1),
        "precip_anomaly_30d_mm": _round(precip_anomaly_30d_mm, 1),
        "precip_anomaly_30d_pct": _round(precip_anomaly_30d_pct, 1),
        "dry_days_30d": int(dry_days_30d),
        "timeseries_30d": timeseries_30d,
        "signals": [
            f"CHIRPS 7d observado: {_round(precip_observed_7d_mm)} mm (fallback sintetico).",
            f"CHIRPS 30d observado: {_round(precip_observed_30d_mm)} mm (fallback sintetico).",
            f"Anomalia 30d: {_round(precip_anomaly_30d_pct, 1)}% (fallback sintetico).",
        ],
    }


def get_climate_history(
    spatial_context: dict[str, Any],
    analysis_timestamp: datetime,
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    use_gee = os.environ.get("USE_GEE_CHIRPS", "true").strip().lower() not in {"0", "false", "no"}
    if use_gee:
        chirps_data = _try_get_gee_chirps_history(
            spatial_context=spatial_context,
            analysis_timestamp=analysis_timestamp,
            geometry=geometry,
        )
        if chirps_data is not None:
            return chirps_data
    return _get_synthetic_climate_history(spatial_context, analysis_timestamp)
