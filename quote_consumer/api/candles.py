from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_404_NOT_FOUND

from quote_consumer.api.dependencies import get_in_memory_storage
from quote_consumer.candle_processor import CandleBuffer
from schemas.types import Candle, Ticker, Timestamp

router = APIRouter()

@router.get("")
async def get_candle(
    ticker: Ticker = Query(...),
    timestamp: Timestamp | None = Query(None),
    in_memory_storage: CandleBuffer = Depends(get_in_memory_storage)
) -> Candle:
    """
    Get the latest candle value for the ticker from the memory if present.
    If timestamp is provided find the quote at exact that timestamp or the closest one.
    """
    if (ticker_buffer := in_memory_storage.get(ticker)) is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="ticker_not_in_memory")

    if not (sorted_timestamps := sorted(ticker_buffer.keys())):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="no_candles_for_ticker")

    # If timestamp is not provided or timestamp is out of upper range return latest candle
    if timestamp is None or timestamp > sorted_timestamps[-1]:
        latest_timestamp = sorted_timestamps[-1]
        return  ticker_buffer[latest_timestamp]

    if candle := ticker_buffer.get(timestamp):
        return candle

    # Return closest timestamp
    for ts in reversed(sorted_timestamps):
        if ts < timestamp:
            return ticker_buffer[ts]

    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="too_old_timestamp")
