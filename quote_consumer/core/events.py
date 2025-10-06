
from types import TracebackType

from fastapi import FastAPI
from loguru import logger

from db.repositories import DB
from quote_consumer.candle_processor import TradesToCandleProcessor
from quote_consumer.core.settings import settings
from quote_consumer.ws_connector.base import RTTradesProvider


class LifeSpan:
    _trds_to_cndl_pr: TradesToCandleProcessor

    def __init__(self, app: FastAPI) -> None:
        self._app = app

    async def __aenter__(self) -> dict:
        logger.info("Stating application")
        await DB.connect(dsn=str(settings.DB_SERVICE))
        await RTTradesProvider.run()
        self._trds_to_cndl_pr = TradesToCandleProcessor(RTTradesProvider.get_trade_queue())
        await self._trds_to_cndl_pr.run()
        self._app.state.in_memory_storage = self._trds_to_cndl_pr.buffer
        return {}

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, traceback: TracebackType | None
    ) -> None:
        logger.info("Stopping application")
        await RTTradesProvider.stop()
        await self._trds_to_cndl_pr.stop()
        await DB.disconnect()
        del self._app.state.in_memory_storage

