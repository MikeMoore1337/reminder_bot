from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from app.config import get_settings

settings = get_settings()


PUBLIC_COMMANDS = [
    BotCommand(command="start", description="Запуск бота"),
    BotCommand(command="help", description="Помощь и примеры"),
    BotCommand(command="timezone", description="Установить часовой пояс"),
    BotCommand(command="mytimezone", description="Показать текущий часовой пояс"),
    BotCommand(command="remind", description="Создать напоминание"),
    BotCommand(command="list", description="Список активных напоминаний"),
    BotCommand(command="cancel", description="Удалить напоминание по ID"),
]

ADMIN_COMMANDS = [
    BotCommand(command="start", description="Запуск бота"),
    BotCommand(command="help", description="Помощь и примеры"),
    BotCommand(command="timezone", description="Установить часовой пояс"),
    BotCommand(command="mytimezone", description="Показать текущий часовой пояс"),
    BotCommand(command="remind", description="Создать напоминание"),
    BotCommand(command="list", description="Список активных напоминаний"),
    BotCommand(command="cancel", description="Удалить напоминание по ID"),
    BotCommand(command="stats", description="Статистика бота"),
    BotCommand(command="failed", description="Ошибки отправки"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        commands=PUBLIC_COMMANDS,
        scope=BotCommandScopeDefault(),
    )

    for admin_id in settings.admin_ids:
        await bot.set_my_commands(
            commands=ADMIN_COMMANDS,
            scope=BotCommandScopeChat(chat_id=admin_id),
        )
