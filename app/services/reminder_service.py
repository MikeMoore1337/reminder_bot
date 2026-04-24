from __future__ import annotations

import calendar
import logging
from datetime import datetime, timedelta
from html import escape
from typing import cast

from sqlalchemy import func, select

from app.db.models import RecurrenceType, Reminder, User
from app.db.session import SessionLocal
from app.utils.datetime_utils import from_utc_to_user, to_utc, utc_now

logger = logging.getLogger(__name__)


def _next_month(dt: datetime) -> datetime:
    year = dt.year + (1 if dt.month == 12 else 0)
    month = 1 if dt.month == 12 else dt.month + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def validate_recurrence(recurrence_type: str, recurrence_interval: int) -> None:
    if recurrence_interval < 1:
        raise ValueError("Интервал повторения должен быть больше 0")

    if recurrence_type == RecurrenceType.MINUTES.value and recurrence_interval < 5:
        raise ValueError("Минимальный интервал для повторения в минутах - 5 минут")

    if (
        recurrence_type
        in {
            RecurrenceType.HOURLY.value,
            RecurrenceType.DAILY.value,
            RecurrenceType.WEEKLY.value,
            RecurrenceType.MONTHLY.value,
        }
        and recurrence_interval < 1
    ):
        raise ValueError("Интервал повторения должен быть не меньше 1")


def calculate_next_occurrence(
    remind_at_utc: datetime,
    recurrence_type: str,
    recurrence_interval: int,
) -> datetime | None:
    if recurrence_type == RecurrenceType.NONE.value:
        return None

    if recurrence_type == RecurrenceType.MINUTES.value:
        return remind_at_utc + timedelta(minutes=recurrence_interval)

    if recurrence_type == RecurrenceType.HOURLY.value:
        return remind_at_utc + timedelta(hours=recurrence_interval)

    if recurrence_type == RecurrenceType.DAILY.value:
        return remind_at_utc + timedelta(days=recurrence_interval)

    if recurrence_type == RecurrenceType.WEEKLY.value:
        return remind_at_utc + timedelta(weeks=recurrence_interval)

    if recurrence_type == RecurrenceType.MONTHLY.value:
        next_dt = remind_at_utc
        for _ in range(recurrence_interval):
            next_dt = _next_month(next_dt)
        return next_dt

    raise ValueError(f"Unsupported recurrence_type: {recurrence_type}")


async def create_reminder(
    user: User,
    local_dt: datetime,
    text: str,
    recurrence_type: str = "none",
    recurrence_interval: int = 1,
) -> Reminder:
    validate_recurrence(recurrence_type, recurrence_interval)

    remind_at_utc = to_utc(local_dt, user.timezone)
    now_utc = utc_now()

    if recurrence_type == RecurrenceType.NONE.value and remind_at_utc <= now_utc:
        raise ValueError("Время напоминания уже прошло")

    if recurrence_type != RecurrenceType.NONE.value:
        while remind_at_utc <= now_utc:
            next_dt = calculate_next_occurrence(
                remind_at_utc,
                recurrence_type,
                recurrence_interval,
            )
            if next_dt is None:
                break
            remind_at_utc = next_dt

    async with SessionLocal() as session:
        reminder = Reminder(
            user_id=user.id,
            chat_id=user.chat_id,
            text=text,
            remind_at_utc=remind_at_utc,
            status="pending",
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
        )
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)

        logger.info(
            "Created reminder",
            extra={
                "extra_data": (
                    f"reminder_id={reminder.id} "
                    f"user_id={user.id} "
                    f"remind_at_utc={reminder.remind_at_utc.isoformat()} "
                    f"recurrence_type={reminder.recurrence_type} "
                    f"recurrence_interval={reminder.recurrence_interval}"
                )
            },
        )
        return reminder


async def list_pending_reminders(user: User) -> list[Reminder]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Reminder)
            .where(
                Reminder.user_id == user.id,
                Reminder.status == "pending",
            )
            .order_by(Reminder.remind_at_utc.asc())
        )
        return list(result.scalars().all())


async def delete_reminder_any_status(user: User, reminder_id: int) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user.id,
            )
        )
        reminder = result.scalar_one_or_none()
        if reminder is None:
            return False

        await session.delete(reminder)
        await session.commit()

        logger.info(
            "Deleted reminder",
            extra={"extra_data": f"reminder_id={reminder_id} user_id={user.id}"},
        )
        return True


async def cancel_reminder(user: User, reminder_id: int) -> bool:
    return await delete_reminder_any_status(user=user, reminder_id=reminder_id)


async def snooze_reminder(user: User, reminder_id: int, minutes: int = 10) -> Reminder | None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user.id,
            )
        )
        reminder = result.scalar_one_or_none()
        if reminder is None:
            return None

        reminder.chat_id = user.chat_id
        reminder.remind_at_utc = utc_now() + timedelta(minutes=minutes)
        reminder.status = "pending"
        reminder.retry_count = 0
        reminder.error_text = None

        await session.commit()
        await session.refresh(reminder)
        return cast(Reminder | None, reminder)


async def set_last_message_id(reminder_id: int, message_id: int | None) -> None:
    async with SessionLocal() as session, session.begin():
        reminder = await session.get(Reminder, reminder_id)
        if reminder is not None:
            reminder.last_message_id = message_id


async def get_stats() -> dict[str, int]:
    async with SessionLocal() as session:
        total_users = await session.scalar(select(func.count()).select_from(User))
        total_reminders = await session.scalar(select(func.count()).select_from(Reminder))
        pending_reminders = await session.scalar(
            select(func.count()).select_from(Reminder).where(Reminder.status == "pending")
        )
        failed_reminders = await session.scalar(
            select(func.count()).select_from(Reminder).where(Reminder.status == "failed")
        )
        recurring_reminders = await session.scalar(
            select(func.count())
            .select_from(Reminder)
            .where(Reminder.recurrence_type != RecurrenceType.NONE.value)
        )
        sent_today = await session.scalar(
            select(func.count())
            .select_from(Reminder)
            .where(
                Reminder.sent_at.is_not(None),
                Reminder.sent_at >= utc_now() - timedelta(days=1),
            )
        )

        return {
            "total_users": total_users or 0,
            "total_reminders": total_reminders or 0,
            "pending_reminders": pending_reminders or 0,
            "failed_reminders": failed_reminders or 0,
            "recurring_reminders": recurring_reminders or 0,
            "sent_last_24h": sent_today or 0,
        }


async def get_failed_reminders(limit: int = 20) -> list[Reminder]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.status == "failed")
            .order_by(Reminder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


def format_recurrence(reminder: Reminder) -> str:
    recurrence_type = str(reminder.recurrence_type)
    interval = int(reminder.recurrence_interval)

    if recurrence_type == RecurrenceType.NONE.value:
        return "нет"

    if recurrence_type == RecurrenceType.MINUTES.value:
        return "каждые 1 минуту" if interval == 1 else f"каждые {interval} минут"

    if recurrence_type == RecurrenceType.HOURLY.value:
        return "каждый час" if interval == 1 else f"каждые {interval} часов"

    if recurrence_type == RecurrenceType.DAILY.value:
        return "каждый день" if interval == 1 else f"каждые {interval} дней"

    if recurrence_type == RecurrenceType.WEEKLY.value:
        return "каждую неделю" if interval == 1 else f"каждые {interval} недель"

    if recurrence_type == RecurrenceType.MONTHLY.value:
        return "каждый месяц" if interval == 1 else f"каждые {interval} месяцев"

    return recurrence_type


def format_reminder_for_user(reminder: Reminder, timezone_name: str) -> str:
    local_dt = from_utc_to_user(reminder.remind_at_utc, timezone_name)
    return (
        f"ID: {reminder.id}\n"
        f"Когда: {local_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Повтор: {format_recurrence(reminder)}\n"
        f"Текст: {escape(reminder.text)}"
    )
