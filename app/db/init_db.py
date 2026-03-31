import logging

logger = logging.getLogger(__name__)


async def init_db() -> None:
    logger.info("init_db skipped - use Alembic migrations")
