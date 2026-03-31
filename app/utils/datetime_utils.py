from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_timezone(timezone_name: str) -> str:
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Неизвестный часовой пояс: {timezone_name}") from exc
    return timezone_name


def to_utc(naive_local_dt: datetime, timezone_name: str) -> datetime:
    tz = ZoneInfo(timezone_name)
    localized = naive_local_dt.replace(tzinfo=tz)
    return localized.astimezone(UTC)


def from_utc_to_user(dt_utc: datetime, timezone_name: str) -> datetime:
    tz = ZoneInfo(timezone_name)
    return dt_utc.astimezone(tz)


def utc_now() -> datetime:
    return datetime.now(UTC)


def now_in_timezone(timezone_name: str) -> datetime:
    tz = ZoneInfo(timezone_name)
    return datetime.now(tz)
