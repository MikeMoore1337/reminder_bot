from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import get_settings

logger = logging.getLogger(__name__)


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def build_web_app(bot: Bot, dispatcher: Dispatcher) -> web.Application:
    settings = get_settings()
    app = web.Application()
    app.router.add_get("/healthz", healthcheck)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.webhook_secret_token,
    )
    webhook_handler.register(app, path=settings.webhook_path)
    setup_application(app, dispatcher, bot=bot)
    logger.info("Webhook app configured", extra={"extra_data": f"path={settings.webhook_path}"})
    return app
