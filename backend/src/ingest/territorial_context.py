import hashlib
import os
from datetime import datetime, timedelta
from typing import Any

from src.ingest.gee_client import get_ee_client, to_ee_polygon
from src.utils.time import ensure_utc, to_iso_z


def _hash_ratio(seed_text: str) -> float:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _reduce_mean(ee: Any, image: Any, geometry: Any, scale: int = 500) -> float | None:
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


def _synthetic_territorial_context(spatial_context: dict[str, Any], analysis_timestamp: datetime) -> dict[str, Any]:
    seed = f"{spatial_context['centroid_lat']}:{spatial_context['centroid_lon']}:{ensure_utc(analysis_timestamp).date()}"
    ndvi = round(0.38 + _hash_ratio(seed + ":ndvi") * 0.34, 3)
    evi = round(0.28 + _hash_ratio(seed + ":evi") * 0.29, 3)
    lst_c = round(30 + _hash_ratio(seed + ":lst") * 8.5, 1)
    cloud_cover = round(5 + _hash_ratio(seed + ":cloud") * 35, 1)

    ndvi_norm = _clamp((0.68 - ndvi) / 0.48, 0.0, 1.0)
    lst_norm = _clamp((lst_c - 28) / 14, 0.0, 1.0)
    vegetation_stress = round(_clamp((0.65 * ndvi_norm) + (0.35 * lst_norm), 0.0, 1.0), 3)
    soil_buffer = round(_clamp((evi - 0.2) / 0.45, 0.0, 1.0), 3)
    vulnerability = round((vegetation_stress * 0.55) + ((1.0 - soil_buffer) * 0.45), 3)

    ndvi_timeseries = []
    base_dt = ensure_utc(analysis_timestamp).replace(hour=0, minute=0, second=0, microsecond=0)
    for idx in range(5):
        dt = base_dt - timedelta(days=(4 - idx) * 10)
        drift = -0.03 * (4 - idx)
        ndvi_timeseries.append({"date": dt.date().isoformat(), "ndvi": round(_clamp(ndvi + drift, 0.1, 0.9), 3)})

    return {
        "source": "synthetic",
        "provider": "SafraViva Synthetic Territory",
        "last_image": to_iso_z(base_dt - timedelta(days=2)),
        "cloud_cover_pct": cloud_cover,
        "ndvi": ndvi,
        "evi": evi,
        "lst_c": lst_c,
        "ndvi_timeseries": ndvi_timeseries,
        "vegetation_stress_index": vegetation_stress,
        "soil_water_buffer_index": soil_buffer,
        "vulnerability_index": vulnerability,
        "alphaearth_cluster": f"mt_cluster_{int(_hash_ratio(seed + ':cluster') * 5) + 1}",
        "signals": [
            f"NDVI medio recente: {ndvi} (fallback sintetico).",
            f"EVI medio recente: {evi} (fallback sintetico).",
            f"LST medio recente: {lst_c} C (fallback sintetico).",
        ],
    }


def _try_get_gee_territorial_context(
    geometry: dict[str, Any],
    spatial_context: dict[str, Any],
    analysis_timestamp: datetime,
) -> dict[str, Any] | None:
    ee, _status = get_ee_client()
    if ee is None:
        return None

    try:
        analysis_utc = ensure_utc(analysis_timestamp)
        end_dt = analysis_utc + timedelta(days=1)
        start_60d = analysis_utc - timedelta(days=60)
        start_30d = analysis_utc - timedelta(days=30)
        polygon = to_ee_polygon(ee, geometry)

        mod13 = (
            ee.ImageCollection("MODIS/061/MOD13Q1")
            .filterBounds(polygon)
            .filterDate(to_iso_z(start_60d), to_iso_z(end_dt))
            .sort("system:time_start")
        )
        if float(mod13.size().getInfo()) == 0:
            return None

        mod13_latest = ee.Image(mod13.sort("system:time_start", False).first())
        ndvi_raw = _reduce_mean(ee, mod13_latest.select(["NDVI"]), polygon, scale=250)
        evi_raw = _reduce_mean(ee, mod13_latest.select(["EVI"]), polygon, scale=250)
        if ndvi_raw is None or evi_raw is None:
            return None

        ndvi = _clamp(ndvi_raw * 0.0001, -0.2, 1.0)
        evi = _clamp(evi_raw * 0.0001, -0.2, 1.0)

        mod11 = (
            ee.ImageCollection("MODIS/061/MOD11A2")
            .filterBounds(polygon)
            .filterDate(to_iso_z(start_30d), to_iso_z(end_dt))
            .sort("system:time_start", False)
        )
        lst_c = 33.0
        if float(mod11.size().getInfo()) > 0:
            mod11_latest = ee.Image(mod11.first())
            lst_raw = _reduce_mean(ee, mod11_latest.select(["LST_Day_1km"]), polygon, scale=1_000)
            if lst_raw is not None:
                lst_c = (lst_raw * 0.02) - 273.15

        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(polygon)
            .filterDate(to_iso_z(start_30d), to_iso_z(end_dt))
        )
        cloud_cover = 15.0
        last_image_iso = to_iso_z(analysis_utc - timedelta(days=2))
        if float(s2.size().getInfo()) > 0:
            cloud_mean = s2.aggregate_mean("CLOUDY_PIXEL_PERCENTAGE").getInfo()
            if cloud_mean is not None:
                cloud_cover = float(cloud_mean)
            last_millis = s2.aggregate_max("system:time_start").getInfo()
            if last_millis:
                last_image_iso = to_iso_z(datetime.utcfromtimestamp(float(last_millis) / 1000.0))

        ndvi_timeseries: list[dict[str, Any]] = []
        mod13_list = mod13.sort("system:time_start", False).limit(5).getInfo().get("features", [])
        for feature in reversed(mod13_list):
            props = feature.get("properties", {})
            ts = props.get("system:time_start")
            if ts:
                date_str = datetime.utcfromtimestamp(float(ts) / 1000.0).date().isoformat()
            else:
                date_str = analysis_utc.date().isoformat()
            image = ee.Image(feature["id"])
            ts_ndvi_raw = _reduce_mean(ee, image.select(["NDVI"]), polygon, scale=250)
            if ts_ndvi_raw is None:
                continue
            ndvi_timeseries.append({"date": date_str, "ndvi": round(_clamp(ts_ndvi_raw * 0.0001, -0.2, 1.0), 3)})

        ndvi_norm = _clamp((0.68 - ndvi) / 0.48, 0.0, 1.0)
        lst_norm = _clamp((lst_c - 28) / 14, 0.0, 1.0)
        vegetation_stress = round(_clamp((0.65 * ndvi_norm) + (0.35 * lst_norm), 0.0, 1.0), 3)
        soil_buffer = round(_clamp((evi - 0.2) / 0.45, 0.0, 1.0), 3)
        vulnerability = round((vegetation_stress * 0.55) + ((1.0 - soil_buffer) * 0.45), 3)

        seed = f"{spatial_context['centroid_lat']}:{spatial_context['centroid_lon']}"
        return {
            "source": "gee",
            "provider": "Google Earth Engine (MODIS/Sentinel-2)",
            "last_image": last_image_iso,
            "cloud_cover_pct": round(cloud_cover, 1),
            "ndvi": round(ndvi, 3),
            "evi": round(evi, 3),
            "lst_c": round(lst_c, 1),
            "ndvi_timeseries": ndvi_timeseries,
            "vegetation_stress_index": vegetation_stress,
            "soil_water_buffer_index": soil_buffer,
            "vulnerability_index": vulnerability,
            "alphaearth_cluster": f"mt_cluster_{int(_hash_ratio(seed + ':cluster') * 5) + 1}",
            "signals": [
                f"NDVI medio recente: {round(ndvi, 3)} (MOD13Q1).",
                f"EVI medio recente: {round(evi, 3)} (MOD13Q1).",
                f"LST medio recente: {round(lst_c, 1)} C (MOD11A2).",
            ],
        }
    except Exception:
        return None


def get_territorial_context(
    geometry: dict[str, Any],
    spatial_context: dict[str, Any],
    analysis_timestamp: datetime,
) -> dict[str, Any]:
    use_gee = os.environ.get("USE_GEE_TERRITORY", "true").strip().lower() not in {"0", "false", "no"}
    if use_gee:
        gee_context = _try_get_gee_territorial_context(geometry, spatial_context, analysis_timestamp)
        if gee_context is not None:
            return gee_context
    return _synthetic_territorial_context(spatial_context, analysis_timestamp)

