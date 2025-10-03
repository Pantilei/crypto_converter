from typing import Any, ClassVar

from aiosonic.client import HTTPClient
from loguru import logger

from currency_conversion.core.settings import settings
from schemas.types import Candle, Ticker, Timestamp


class InMemoryQuoteServiceError(Exception):
    ...


class InMemoryQuoteService:
    _http_client: ClassVar[HTTPClient] = HTTPClient()

    @classmethod
    async def get_in_memory_candle(
        cls, ticker: Ticker, timestamp: Timestamp | None = None
    ) -> Candle:
        """Get ticker price. If timestamp is None latest price is returned"""
        params: dict[str, Any] = {"ticker": ticker}
        if timestamp:
            params |= {"timestamp": timestamp}
        try:
            resp = await cls._http_client.get(f"{settings.QUOTE_CONSUMER_SERVICE}candles", params=params)
        except Exception as ex:
            logger.error(f"Service {cls.__name__} not working.")
            raise InMemoryQuoteServiceError from ex
    
        if not resp.ok:
            raise InMemoryQuoteServiceError

        return Candle.model_validate(await resp.json())
