from __future__ import annotations

import asyncio
import logging

from app.bot_factory import create_bot
from app.config import get_settings
from app.logging_config import setup_logging
from app.workers.reminder_worker import reminder_loop

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting reminder worker application")
    bot = create_bot()
    try:
        await reminder_loop(bot)
    finally:
        await bot.session.close()
        logger.info("Reminder worker application stopped")


if __name__ == "__main__":
    asyncio.run(main())
