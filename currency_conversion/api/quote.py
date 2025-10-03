from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from currency_conversion.services.quote_consumer import (
    InMemoryQuoteService,
    InMemoryQuoteServiceError,
)
from db.repositories import DB
from schemas.types import Ticker, Timestamp

router = APIRouter()


class _Quote(BaseModel):
    amount: Decimal
    conversion_rate: Decimal


@router.get("", responses={HTTP_404_NOT_FOUND: {"model": None, "description": "For outdated prices or missing prices"}})
async def get_quote(
    amount: Decimal = Query(..., gt=0),
    from_: str = Query(..., alias="from", example="BTC"),
    to: str = Query(..., example="USDT"),
    timestamp: Timestamp | None = Query(None), 
) -> _Quote:
    """
    Get Quote of conversion from latest price.
    In case if timestamp is specified, will use closest to provided timestamp price
    """
    # NOTE: Assuming for now that only Binance exchange exists
    ticker = Ticker.build(f"{from_.upper()}{to.upper()}", "BINANCE")
    try:
        candle = await InMemoryQuoteService.get_in_memory_candle(ticker, timestamp)
    except InMemoryQuoteServiceError:
        candle = await DB.candles_1s.get_latest_candle(ticker=ticker, timestamp=timestamp)
    
    if candle is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="conversion_not_possible")
    
    if timestamp is None and candle.t < datetime.now(tz=UTC) - timedelta(minutes=1):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="quotes_outdated")
    
    return _Quote(amount=amount*candle.c, conversion_rate=candle.c)
