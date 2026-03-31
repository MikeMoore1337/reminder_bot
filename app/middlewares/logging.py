from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update

logger = logging.getLogger(__name__)


class UpdateLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update = data.get("event_update")
        if isinstance(update, Update):
            message = update.message or update.edited_message
            if isinstance(message, Message) and message.from_user:
                logger.info(
                    "Incoming update",
                    extra={
                        "extra_data": (
                            f"user_id={message.from_user.id} chat_id={message.chat.id} "
                            f"text={message.text!r}"
                        )
                    },
                )
        return await handler(event, data)
