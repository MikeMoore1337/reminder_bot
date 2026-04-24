from __future__ import annotations

import logging

from sqlalchemy import select

from app.config import get_settings
from app.db.models import User
from app.db.session import SessionLocal
from app.utils.datetime_utils import validate_timezone

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_or_create_user(telegram_user_id: int, chat_id: int) -> User:
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                timezone=settings.default_timezone,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(
                "Created user",
                extra={
                    "extra_data": f"telegram_user_id={telegram_user_id} timezone={user.timezone}"
                },
            )
            return user

        if user.chat_id != chat_id:
            user.chat_id = chat_id
            await session.commit()

        return user


async def set_user_timezone(telegram_user_id: int, chat_id: int, timezone_name: str) -> User:
    timezone_name = validate_timezone(timezone_name)

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                timezone=timezone_name,
            )
            session.add(user)
        else:
            user.timezone = timezone_name
            user.chat_id = chat_id

        await session.commit()
        await session.refresh(user)
        logger.info(
            "Updated timezone",
            extra={"extra_data": f"telegram_user_id={telegram_user_id} timezone={timezone_name}"},
        )
        return user


async def get_user_timezone(telegram_user_id: int, chat_id: int) -> str:
    user = await get_or_create_user(telegram_user_id=telegram_user_id, chat_id=chat_id)
    return user.timezone
