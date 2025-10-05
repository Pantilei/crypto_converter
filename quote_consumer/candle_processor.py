import asyncio
import traceback
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from time import monotonic

from loguru import logger

from db.repositories import DB
from quote_consumer.core.settings import settings
from schemas.types import Candle, Ticker, Timestamp, Trade

type CandleBuffer = dict[Ticker, dict[Timestamp, Candle]]


class TradesToCandleProcessor:
    def __init__(self, data_provider: asyncio.Queue[Trade]) -> None:
        self._configs = settings.TRADES_TO_CANDLES_CONFIG
        self._data_provider = data_provider
        self._storage_buffer: CandleBuffer = defaultdict(dict)
        self._tickers_with_updated_prices: dict[Ticker, set[Timestamp]] = defaultdict(set)
        self._background_tasks: list[asyncio.Task[None]] = []

    @property
    def buffer(self) -> CandleBuffer:
        return self._storage_buffer

    async def run(self) -> None:
        # TODO: Load from database initial state
        await self._load_buffer()
        self._background_tasks.extend([
            asyncio.create_task(self._periodic_flusher_to_db()),
            asyncio.create_task(self._periodic_old_candles_remover()),
            asyncio.create_task(self._periodic_buffer_cleaner()),
            asyncio.create_task(self._trades_to_buffer_processor())
        ])

    async def stop(self) -> None:
        for tsk in self._background_tasks:
            tsk.cancel()
        await self._flush()

    async def _trades_to_buffer_processor(self) -> None:
        while trade := await self._data_provider.get():
            aligned_t = Timestamp(trade.t // 1000)  # Milliseconds alined to seconds
            # Used to control which candles must be flushed to DB
            self._tickers_with_updated_prices[trade.T].add(aligned_t)
            ticker_buffer = self._storage_buffer[trade.T]
            if (candle := ticker_buffer.get(aligned_t)) is None:
                ticker_buffer[aligned_t] = trade.to_candle()
                continue
            candle.update(trade)

    async def _periodic_buffer_cleaner(self) -> None:
        while True:
            await asyncio.sleep(self._configs.buffer_clean_period)
            remove_till = datetime.now(tz=UTC).timestamp() - self._configs.buffer_interval
            to_remove_count = 0
            for ts_to_candle in self._storage_buffer.values():
                ts_to_remove: list[Timestamp] = []
                for ts in ts_to_candle:
                    if ts <= remove_till:
                        ts_to_remove.append(ts)
                        to_remove_count += 1

                for ts in ts_to_remove:
                    ts_to_candle.pop(ts, None)

            msg = f"Buffer removed candles count: {to_remove_count}. Tickers in buffer: {len(self._storage_buffer)}"
            logger.info(msg)

    async def _periodic_flusher_to_db(self) -> None:
        while True:
            await asyncio.sleep(self._configs.flush_to_db_period)
            await self._flush()

    async def _periodic_old_candles_remover(self) -> None:
        while True:
            await asyncio.sleep(self._configs.storage_clean_period)
            t_start = monotonic()
            del_till = datetime.now(tz=UTC) - timedelta(days=self._configs.storage_max_interval)
            logger.info(f"Removing candles older than {del_till}")
            try:
                await DB.candles_1s.remove_old_candles(del_till)
            except Exception:
                logger.error("Cannot remove old candles from storage.")
                logger.error(traceback.format_exc())
                continue
            logger.info(f"Removed in {timedelta(seconds=monotonic() - t_start)}s")

    def _get_flushable_candles(self) -> Iterable[Candle]:
        candles_count = 0
        for ticker, tss in self._tickers_with_updated_prices.items():
            for ts in tss:
                if ts not in self._storage_buffer[ticker]:
                    continue
                candles_count += 1
                yield self._storage_buffer[ticker][ts]
        # Restore the state
        tkrs_updt_price = len(self._tickers_with_updated_prices)
        logger.info(f"Candles to flush: {candles_count}. Tickers: {tkrs_updt_price}")
        self._tickers_with_updated_prices = defaultdict(set)

    async def _flush(self) -> None:
        t_start = monotonic()
        try:
            await DB.candles_1s.bulk_upsert(self._get_flushable_candles())
        except Exception:
            logger.error("Cannot flush to storage")
            logger.error(traceback.format_exc())
            return
        logger.info(f"Flushed in: {timedelta(seconds=monotonic() - t_start)}")

    async def _load_buffer(self) -> None:
        cdl_count, t_start = 0, monotonic()
        from_ = datetime.now(UTC) - timedelta(seconds=self._configs.buffer_interval)
        async for cdl in DB.candles_1s.get_candles(from_=from_):
            self._storage_buffer[cdl.T][Timestamp.from_dt(cdl.t)] = cdl
            cdl_count += 1
        logger.info(f"Candles loaded: {cdl_count}. In: {timedelta(seconds=monotonic() - t_start)}s")

