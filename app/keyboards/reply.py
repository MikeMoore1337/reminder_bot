from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Создать напоминание"),
                KeyboardButton(text="📋 Мои напоминания"),
            ],
            [
                KeyboardButton(text="🌍 Часовой пояс"),
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Например: напомни завтра в 9 созвон",
    )


def get_timezone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Europe/Moscow"),
                KeyboardButton(text="Europe/Helsinki"),
            ],
            [
                KeyboardButton(text="Europe/Berlin"),
                KeyboardButton(text="UTC"),
            ],
            [
                KeyboardButton(text="⬅️ Назад"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери часовой пояс или введи свой, например Europe/Moscow",
    )
