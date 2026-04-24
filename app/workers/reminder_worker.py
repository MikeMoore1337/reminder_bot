from __future__ import annotations

import asyncio
import logging
from html import escape

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from app.config import get_settings
from app.db.models import RecurrenceType, Reminder
from app.db.session import SessionLocal
from app.services.reminder_service import calculate_next_occurrence, set_last_message_id
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)
settings = get_settings()


def reminder_actions_kb(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отложить на 10 минут", callback_data=f"reminder:snooze:{reminder_id}"
                ),
                InlineKeyboardButton(
                    text="Удалить", callback_data=f"reminder:delete:{reminder_id}"
                ),
            ]
        ]
    )


async def fetch_due_reminders(limit: int) -> list[Reminder]:
    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Reminder)
                .where(
                    Reminder.status == "pending",
                    Reminder.remind_at_utc <= utc_now(),
                )
                .order_by(Reminder.remind_at_utc.asc())
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
            reminders = list(result.scalars().all())

            for reminder in reminders:
                reminder.status = "processing"

        return reminders


async def mark_after_send(reminder_id: int) -> None:
    async with SessionLocal() as session, session.begin():
        reminder = await session.get(Reminder, reminder_id)
        if reminder is None:
            return
        reminder.sent_at = utc_now()
        reminder.error_text = None
        reminder.retry_count = 0

        if reminder.recurrence_type == RecurrenceType.NONE.value:
            reminder.status = "sent"
            return

        next_occurrence = calculate_next_occurrence(
            reminder.remind_at_utc,
            reminder.recurrence_type,
            reminder.recurrence_interval,
        )
        if next_occurrence is None:
            reminder.status = "sent"
            return
        while next_occurrence <= utc_now():
            future_occurrence = calculate_next_occurrence(
                next_occurrence,
                reminder.recurrence_type,
                reminder.recurrence_interval,
            )
            if future_occurrence is None:
                break
            next_occurrence = future_occurrence
        reminder.remind_at_utc = next_occurrence
        reminder.status = "pending"


async def mark_failed(reminder_id: int, error_text: str) -> None:
    async with SessionLocal() as session, session.begin():
        reminder = await session.get(Reminder, reminder_id)
        if reminder is None:
            return
        reminder.retry_count += 1
        reminder.status = "pending" if reminder.retry_count < 3 else "failed"
        reminder.error_text = error_text[:2000]


async def process_due_reminders(bot: Bot) -> int:
    reminders = await fetch_due_reminders(limit=settings.worker_batch_size)
    if not reminders:
        return 0

    processed_count = 0
    for reminder in reminders:
        try:
            sent = await bot.send_message(
                chat_id=reminder.chat_id,
                text=f"⏰ Напоминание\n\n{escape(reminder.text)}",
                reply_markup=reminder_actions_kb(reminder.id),
            )
            await set_last_message_id(reminder.id, sent.message_id)
            await mark_after_send(reminder.id)
            processed_count += 1
            logger.info(
                "Reminder sent",
                extra={"extra_data": f"reminder_id={reminder.id} chat_id={reminder.chat_id}"},
            )
        except Exception as exc:
            await mark_failed(reminder.id, str(exc))
            logger.exception(
                "Failed to send reminder",
                extra={"extra_data": f"reminder_id={reminder.id} chat_id={reminder.chat_id}"},
            )

    return processed_count


async def reminder_loop(bot: Bot) -> None:
    logger.info("Reminder worker started")
    while True:
        try:
            processed_count = await process_due_reminders(bot)
            if processed_count:
                logger.info("Processed reminders", extra={"extra_data": f"count={processed_count}"})
        except Exception:
            logger.exception("Unexpected error in reminder worker loop")
        await asyncio.sleep(settings.worker_poll_interval_seconds)
