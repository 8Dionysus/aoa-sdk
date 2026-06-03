"""Timestamp normalization helpers for checkpoint records."""

from __future__ import annotations

from datetime import UTC, datetime


def local_timestamp_parts(now_utc: datetime | None = None) -> tuple[datetime, str, str]:
    canonical_utc = now_utc or datetime.now(UTC)
    local_now = canonical_utc.astimezone()
    local_tz = local_now.tzname() or local_now.strftime("%z")
    return canonical_utc, local_now.isoformat(), local_tz


def coerce_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def with_local_timestamp_default(
    *,
    utc_value: datetime | str | None,
    local_value: str | None,
    tz_name: str | None,
) -> tuple[str | None, str | None]:
    if local_value is not None and tz_name is not None:
        return local_value, tz_name
    parsed = coerce_datetime(utc_value)
    if parsed is None:
        return local_value, tz_name
    local_now = parsed.astimezone()
    return local_value or local_now.isoformat(), tz_name or local_now.tzname() or local_now.strftime("%z")


def utc_timestamp(now_utc: datetime | None = None) -> str:
    canonical_utc = now_utc or datetime.now(UTC)
    return canonical_utc.isoformat().replace("+00:00", "Z")


def observed_timestamp_fields(now_utc: datetime | None = None) -> dict[str, str]:
    canonical_utc, observed_at_local, observed_tz = local_timestamp_parts(now_utc)
    return {
        "observed_at": utc_timestamp(canonical_utc),
        "observed_at_local": observed_at_local,
        "observed_tz": observed_tz,
    }
