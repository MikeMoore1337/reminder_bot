from aiogram import Bot, Dispatcher

from app.config import get_settings
from app.handlers.common import router as common_router
from app.handlers.reminders import router as reminders_router
from app.middlewares.logging import UpdateLoggingMiddleware


def create_bot() -> Bot:
    settings = get_settings()
    return Bot(token=settings.bot_token)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(UpdateLoggingMiddleware())
    dp.include_router(common_router)
    dp.include_router(reminders_router)
    return dp
