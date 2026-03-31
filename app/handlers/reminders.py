from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import get_settings
from app.services.reminder_parser import parse_reminder_input
from app.services.reminder_service import (
    cancel_reminder,
    create_reminder,
    format_reminder_for_user,
    get_failed_reminders,
    get_stats,
    list_pending_reminders,
    snooze_reminder,
)
from app.services.timezone_service import get_or_create_user
from app.utils.datetime_utils import from_utc_to_user, now_in_timezone

router = Router()
settings = get_settings()


def reminder_actions_kb(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отложить на 10 минут", callback_data=f"reminder:snooze:{reminder_id}"),
                InlineKeyboardButton(text="Удалить", callback_data=f"reminder:delete:{reminder_id}"),
            ]
        ]
    )


def is_admin(telegram_user_id: int) -> bool:
    return telegram_user_id in settings.admin_ids


async def _create_and_answer(message: Message) -> None:
    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
    )
    now_local = now_in_timezone(user.timezone)
    parsed = parse_reminder_input(message.text or "", now_local=now_local)
    if parsed is None:
        return

    try:
        reminder = await create_reminder(
            user=user,
            local_dt=parsed.local_dt,
            text=parsed.text,
            recurrence_type=parsed.recurrence_type,
            recurrence_interval=parsed.recurrence_interval,
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return

    local_dt = from_utc_to_user(reminder.remind_at_utc, user.timezone)
    repetition = "нет" if parsed.recurrence_type == "none" else parsed.recurrence_type
    labels = {"daily": "каждый день", "weekly": "каждую неделю", "monthly": "каждый месяц", "none": "нет"}
    await message.answer(
        "Напоминание сохранено.\n"
        f"ID: {reminder.id}\n"
        f"Когда: {local_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Повтор: {labels.get(repetition, repetition)}\n"
        f"Текст: {reminder.text}\n"
        f"Часовой пояс: {user.timezone}"
    )


@router.message(Command("remind"))
async def cmd_remind(message: Message) -> None:
    if parse_reminder_input(message.text or "", now_local=now_in_timezone((await get_or_create_user(message.from_user.id, message.chat.id)).timezone)) is None:
        await message.answer(
            "Не понял формат. Используй, например:\n"
            "/remind 2026-03-31 18:30 Купить молоко\n"
            "напомни завтра в 9 созвон\n"
            "напомни через 2 часа выключить духовку\n"
            "напомни каждый день в 9 выпить витамины"
        )
        return
    await _create_and_answer(message)


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
    )
    reminders = await list_pending_reminders(user)
    if not reminders:
        await message.answer("Активных напоминаний нет")
        return

    text = "\n\n".join(format_reminder_for_user(item, user.timezone) for item in reminders[:20])
    if len(reminders) > 20:
        text += f"\n\nПоказаны первые 20 из {len(reminders)}"
    await message.answer(text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй так: /cancel 12")
        return

    reminder_id = int(parts[1])
    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
    )
    deleted = await cancel_reminder(user=user, reminder_id=reminder_id)
    if deleted:
        await message.answer(f"Напоминание {reminder_id} удалено")
    else:
        await message.answer("Напоминание с таким id не найдено")


@router.callback_query(F.data.startswith("reminder:"))
async def reminder_callback(callback: CallbackQuery) -> None:
    _, action, reminder_id_raw = callback.data.split(":", maxsplit=2)
    if not reminder_id_raw.isdigit():
        await callback.answer("Некорректный id", show_alert=True)
        return

    reminder_id = int(reminder_id_raw)
    user = await get_or_create_user(
        telegram_user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
    )

    if action == "delete":
        deleted = await cancel_reminder(user=user, reminder_id=reminder_id)
        await callback.answer("Удалено" if deleted else "Уже удалено", show_alert=False)
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
        return

    if action == "snooze":
        reminder = await snooze_reminder(user=user, reminder_id=reminder_id, minutes=10)
        if reminder is None:
            await callback.answer("Напоминание не найдено", show_alert=True)
            return
        local_dt = from_utc_to_user(reminder.remind_at_utc, user.timezone)
        await callback.answer("Отложено на 10 минут", show_alert=False)
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(
                f"Напоминание {reminder.id} отложено до {local_dt.strftime('%d.%m.%Y %H:%M')}"
            )
        return

    await callback.answer("Неизвестное действие", show_alert=True)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору")
        return
    stats = await get_stats()
    await message.answer(
        "Статистика:\n"
        f"Пользователи: {stats['total_users']}\n"
        f"Всего напоминаний: {stats['total_reminders']}\n"
        f"Активные: {stats['pending_reminders']}\n"
        f"Повторяющиеся: {stats['recurring_reminders']}\n"
        f"Ошибки: {stats['failed_reminders']}\n"
        f"Отправлено за 24 часа: {stats['sent_last_24h']}"
    )


@router.message(Command("failed"))
async def cmd_failed(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору")
        return
    reminders = await get_failed_reminders(limit=20)
    if not reminders:
        await message.answer("Неудачных отправок нет")
        return
    chunks = []
    for item in reminders:
        chunks.append(
            f"ID: {item.id}\nchat_id: {item.chat_id}\nretry_count: {item.retry_count}\nошибка: {(item.error_text or '-')[:300]}"
        )
    await message.answer("\n\n".join(chunks))


@router.message()
async def text_reminder_handler(message: Message) -> None:
    await _create_and_answer(message)
