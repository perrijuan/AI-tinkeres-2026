from datetime import datetime, timedelta, timezone


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_iso_z(value: datetime) -> str:
    return ensure_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def latest_gfs_run_timestamp(analysis_timestamp: datetime) -> datetime:
    ts = ensure_utc(analysis_timestamp)
    cycle_hour = (ts.hour // 6) * 6
    run_ts = ts.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
    if run_ts > ts:
        run_ts = run_ts - timedelta(hours=6)
    return run_ts

