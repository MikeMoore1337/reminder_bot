from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update

logger = logging.getLogger(__name__)


class UpdateLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
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
