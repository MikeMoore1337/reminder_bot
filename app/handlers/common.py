from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.timezone_service import get_or_create_user, get_user_timezone, set_user_timezone
from app.utils.datetime_utils import validate_timezone

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user = await get_or_create_user(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
    )
    await message.answer(
        "Привет. Я бот-напоминалка.\n\n"
        "Команды:\n"
        "/timezone Europe/Moscow - установить часовой пояс\n"
        "/mytimezone - показать текущий часовой пояс\n"
        "/remind 2026-03-31 18:30 Купить молоко\n"
        "/list - список активных напоминаний\n"
        "/cancel 12 - удалить напоминание\n/stats - статистика для админа\n/failed - failed для админа\n\n"
        f"Твой текущий часовой пояс: {user.timezone}"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Примеры:\n"
        "/timezone Europe/Moscow\n"
        "/remind 2026-03-31 18:30 Позвонить маме\n"
        "напомни 31.03.2026 18:30 Позвонить маме\n"
        "напомни завтра в 9 позвонить маме\n"
        "напомни через 30 минут выключить духовку\n"
        "напомни каждый день в 9 выпить витамины"
    )


@router.message(Command("timezone"))
async def cmd_timezone(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Укажи часовой пояс так:\n/timezone Europe/Moscow")
        return

    timezone_name = parts[1].strip()
    try:
        validate_timezone(timezone_name)
    except ValueError:
        await message.answer(
            "Неизвестный часовой пояс. Используй формат вроде:\n"
            "Europe/Moscow\nEurope/Helsinki\nAsia/Yekaterinburg"
        )
        return

    user = await set_user_timezone(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
        timezone_name=timezone_name,
    )
    await message.answer(f"Часовой пояс сохранён: {user.timezone}")


@router.message(Command("mytimezone"))
async def cmd_mytimezone(message: Message) -> None:
    timezone_name = await get_user_timezone(
        telegram_user_id=message.from_user.id,
        chat_id=message.chat.id,
    )
    await message.answer(f"Твой текущий часовой пояс: {timezone_name}")
