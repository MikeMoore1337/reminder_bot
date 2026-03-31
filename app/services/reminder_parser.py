from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from app.db.models import RecurrenceType

Recurrence = Literal["none", "daily", "weekly", "monthly"]

REMIND_COMMAND_RE = re.compile(
    r"^/remind\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s+(.+)$",
    flags=re.IGNORECASE,
)

REMIND_TEXT_RE = re.compile(
    r"^напомни\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{1,2}:\d{2})\s+(.+)$",
    flags=re.IGNORECASE,
)

TODAY_RE = re.compile(r"^напомни\s+сегодня\s+в\s+(\d{1,2})(?::(\d{2}))?\s+(.+)$", re.IGNORECASE)
TOMORROW_RE = re.compile(r"^напомни\s+завтра\s+в\s+(\d{1,2})(?::(\d{2}))?\s+(.+)$", re.IGNORECASE)
IN_HOURS_RE = re.compile(r"^напомни\s+через\s+(\d+)\s+час(?:а|ов)?\s+(.+)$", re.IGNORECASE)
IN_MINUTES_RE = re.compile(r"^напомни\s+через\s+(\d+)\s+мин(?:ут|уты|уту)?\s+(.+)$", re.IGNORECASE)
EVERY_DAY_RE = re.compile(
    r"^напомни\s+каждый\s+день\s+в\s+(\d{1,2})(?::(\d{2}))?\s+(.+)$", re.IGNORECASE
)
EVERY_WEEK_RE = re.compile(
    r"^напомни\s+каждую\s+неделю\s+в\s+(\d{1,2})(?::(\d{2}))?\s+(.+)$", re.IGNORECASE
)
EVERY_MONTH_RE = re.compile(
    r"^напомни\s+каждый\s+месяц\s+в\s+(\d{1,2})(?::(\d{2}))?\s+(.+)$", re.IGNORECASE
)


@dataclass(slots=True)
class ParsedReminder:
    local_dt: datetime
    text: str
    recurrence_type: Recurrence = "none"
    recurrence_interval: int = 1


def _build_time(base_dt: datetime, hour: str, minute: str | None) -> datetime:
    return base_dt.replace(hour=int(hour), minute=int(minute or 0), second=0, microsecond=0)


def parse_reminder_input(raw_text: str, now_local: datetime) -> ParsedReminder | None:
    text = raw_text.strip()

    command_match = REMIND_COMMAND_RE.match(text)
    if command_match:
        date_part, time_part, reminder_text = command_match.groups()
        local_dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        return ParsedReminder(local_dt=local_dt, text=reminder_text.strip())

    text_match = REMIND_TEXT_RE.match(text)
    if text_match:
        date_part, time_part, reminder_text = text_match.groups()
        local_dt = datetime.strptime(f"{date_part} {time_part}", "%d.%m.%Y %H:%M")
        return ParsedReminder(local_dt=local_dt, text=reminder_text.strip())

    m = TODAY_RE.match(text)
    if m:
        hour, minute, reminder_text = m.groups()
        return ParsedReminder(
            local_dt=_build_time(now_local, hour, minute), text=reminder_text.strip()
        )

    m = TOMORROW_RE.match(text)
    if m:
        hour, minute, reminder_text = m.groups()
        base_dt = now_local + timedelta(days=1)
        return ParsedReminder(
            local_dt=_build_time(base_dt, hour, minute), text=reminder_text.strip()
        )

    m = IN_HOURS_RE.match(text)
    if m:
        hours, reminder_text = m.groups()
        dt = now_local + timedelta(hours=int(hours))
        return ParsedReminder(
            local_dt=dt.replace(second=0, microsecond=0), text=reminder_text.strip()
        )

    m = IN_MINUTES_RE.match(text)
    if m:
        minutes, reminder_text = m.groups()
        dt = now_local + timedelta(minutes=int(minutes))
        return ParsedReminder(
            local_dt=dt.replace(second=0, microsecond=0), text=reminder_text.strip()
        )

    m = EVERY_DAY_RE.match(text)
    if m:
        hour, minute, reminder_text = m.groups()
        dt = _build_time(now_local, hour, minute)
        return ParsedReminder(local_dt=dt, text=reminder_text.strip(), recurrence_type="daily")

    m = EVERY_WEEK_RE.match(text)
    if m:
        hour, minute, reminder_text = m.groups()
        dt = _build_time(now_local, hour, minute)
        return ParsedReminder(local_dt=dt, text=reminder_text.strip(), recurrence_type="weekly")

    m = EVERY_MONTH_RE.match(text)
    if m:
        hour, minute, reminder_text = m.groups()
        dt = _build_time(now_local, hour, minute)
        return ParsedReminder(local_dt=dt, text=reminder_text.strip(), recurrence_type="monthly")

    return None


def parse_recurrence(text: str):
    text = text.lower()

    # каждые X минут
    m = re.search(r"каждые\s+(\d+)\s+минут", text)
    if m:
        return RecurrenceType.MINUTES.value, int(m.group(1))

    # каждый час
    if "каждый час" in text:
        return RecurrenceType.HOURLY.value, 1

    # каждые X часов
    m = re.search(r"каждые\s+(\d+)\s+час", text)
    if m:
        return RecurrenceType.HOURLY.value, int(m.group(1))

    # день
    if "каждый день" in text:
        return RecurrenceType.DAILY.value, 1

    # неделя
    if "каждую неделю" in text:
        return RecurrenceType.WEEKLY.value, 1

    # месяц
    if "каждый месяц" in text:
        return RecurrenceType.MONTHLY.value, 1

    return RecurrenceType.NONE.value, 1
