from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_settings
from app.services.reminder_service import get_failed_reminders, get_stats

router = Router()
settings = get_settings()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔ Команда доступна только администратору.")
        return

    stats = await get_stats()

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👤 Пользователей: <b>{stats['total_users']}</b>\n"
        f"📝 Всего напоминаний: <b>{stats['total_reminders']}</b>\n"
        f"⏳ Ожидают: <b>{stats['pending_reminders']}</b>\n"
        f"❌ Ошибок: <b>{stats['failed_reminders']}</b>\n"
        f"🔁 Повторяющихся: <b>{stats['recurring_reminders']}</b>\n"
        f"✅ Отправлено за 24 часа: <b>{stats['sent_last_24h']}</b>"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("failed"))
async def cmd_failed(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("⛔ Команда доступна только администратору.")
        return

    reminders = await get_failed_reminders()

    if not reminders:
        await message.answer("✅ Ошибок отправки сейчас нет.")
        return

    parts: list[str] = ["❌ <b>Последние failed-напоминания</b>\n"]

    for reminder in reminders:
        reminder_text = escape(reminder.text[:300])
        error_text = escape((reminder.error_text or "-")[:500])
        parts.append(
            f"ID: <b>{reminder.id}</b>\n"
            f"user_id: <code>{reminder.user_id}</code>\n"
            f"chat_id: <code>{reminder.chat_id}</code>\n"
            f"when_utc: <code>{reminder.remind_at_utc.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
            f"text: {reminder_text}\n"
            f"error: <code>{error_text}</code>\n"
        )

    await message.answer("\n".join(parts), parse_mode="HTML")
