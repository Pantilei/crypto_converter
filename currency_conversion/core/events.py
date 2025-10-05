
from types import TracebackType

from fastapi import FastAPI
from loguru import logger

from currency_conversion.core.settings import settings
from db.repositories import DB


class LifeSpan:
    def __init__(self, app: FastAPI) -> None:
        self._app = app

    async def __aenter__(self) -> dict:
        logger.info("Stating application")
        await DB.connect(dsn=str(settings.DB_SERVICE))
        return {}

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, traceback: TracebackType | None
    ) -> None:
        logger.info("Stopping application")
        await DB.disconnect()

