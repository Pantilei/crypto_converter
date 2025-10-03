from datetime import UTC, datetime
from typing import AsyncIterable, Iterable

from db.queries.queries import queries
from db.repositories.base import BaseRepo
from db.repositories.candles_1s.schema import CandleDB
from schemas.types import Candle, Ticker, Timestamp


class Candles1sRepo(BaseRepo):
    async def bulk_upsert(self, candles: Iterable[Candle]) -> None:
        if not (db_candles := [_candle_to_db(cndl) for cndl in candles]):
            return
        await queries.bulk_upsert_candles(self.pool, db_candles)
    
    async def remove_old_candles(self, to: datetime) -> None:
        await queries.remove_old_candles(self.pool, till=to)

    async def get_latest_candle(self, ticker: Ticker, *, timestamp: Timestamp | None = None) -> Candle | None:
        if timestamp is None:
            timestamp = Timestamp.now()
        if not (rec := await queries.get_latest_candle(self.pool, ticker=ticker, till_dt=timestamp.to_dt())):
            return None
        return _db_candle_to_candle(rec)
    
    async def get_candles(self, from_: datetime, to: datetime | None = None) -> AsyncIterable[Candle]:
        if to is None:
            to = datetime.now(tz=UTC)
        async with queries.get_candles_in_range_cursor(self.pool, from_=from_, to=to) as cursor:
            async for row in cursor:
                yield _db_candle_to_candle(row)


def _candle_to_db(candle: Candle) -> CandleDB:
    return CandleDB(
        ticker=candle.T,
        t=candle.t,
        open=candle.o,
        close=candle.c,
        high=candle.h,
        low=candle.l,
        volume=candle.v,
    )

def _db_candle_to_candle(candle_db: CandleDB) -> Candle:
    return Candle(
        T=Ticker(candle_db["ticker"]),
        t=candle_db["t"],
        o=candle_db["open"],
        c=candle_db["close"],
        h=candle_db["high"],
        l=candle_db["low"],
        v=candle_db["volume"],
    )