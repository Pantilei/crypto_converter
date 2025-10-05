from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum
from itertools import batched
from typing import ClassVar, TypedDict
from uuid import uuid4

import ujson
from aiosonic.client import HTTPClient
from loguru import logger

from quote_consumer.ws_connector.base import BaseTradePayload, RTTradesProvider
from schemas.types import Symbol, Ticker, Timestamp, Trade


class BinanceMsgType(StrEnum):
    subscribe = "SUBSCRIBE"
    unsubscribe = "UNSUBSCRIBE"


class BinanceStreamSubMsg(TypedDict):
    method: BinanceMsgType
    params: list[str]
    id: str


class BinanceTradePayload(BaseTradePayload):
    e: str     # Event type
    E: int     # Event time
    s: Symbol  # Symbol
    a: int     # Aggregate trade ID
    p: Decimal # Price
    q: Decimal # Quantity
    f: int     # First trade ID
    l: int     # Last trade ID
    T: int     # Trade time in milliseconds
    m: bool    # Is the buyer the market maker?
    M: bool    # Ignore

    def to_trade(self) -> Trade:
        return Trade(
            t=Timestamp(self.T),
            T=Ticker.build(self.s, "BINANCE"),
            p=self.p,
            v=self.q
        )


class BinanceRTTradesProvider(RTTradesProvider[BinanceTradePayload]):
    ws_url: ClassVar[str] = "wss://stream.binance.com:9443/ws"

    # NOTE: According to binance docs N_STREAM is 1024 but it does not broadcast trades
    N_STREAMS: ClassVar[int] = 1024  # Maximum number of stream per connection
    MAX_SUBS_PER_MESSAGE: ClassVar[int] = 200
    SUB_DELAY: ClassVar[float] = 0.3  # Subscriptions messages sending rate
    exchange_info_url: ClassVar[str] = "https://api.binance.com/api/v3/exchangeInfo"
    http_client: ClassVar[HTTPClient] = HTTPClient()

    async def get_conn_sub_message(self) -> Iterable[tuple[list[BinanceStreamSubMsg], float | None]]:  # type: ignore
        logger.info("Fetching all available symbols...")
        resp = await self.http_client.get(self.exchange_info_url)
        symbols = sorted(r["symbol"] for r in (await resp.json(json_decoder=ujson.loads))["symbols"])
        logger.info(f"Symbols {len(symbols)} fetched.")
        sub_messages_per_conn: list[tuple[list[BinanceStreamSubMsg], float | None]] = []
        for batch_per_connection in batched(symbols, self.N_STREAMS):
            sub_messages_of_conn: list[BinanceStreamSubMsg] = []
            for batch_per_subscription in batched(batch_per_connection, self.MAX_SUBS_PER_MESSAGE):
                sub_msg_id = str(uuid4())
                params = [f"{str(sym).lower()}@aggTrade" for sym in batch_per_subscription]
                sub_messages_of_conn.append(
                    BinanceStreamSubMsg(method=BinanceMsgType.subscribe, params=params, id=sub_msg_id)
                )
            sub_messages_per_conn.append((sub_messages_of_conn, self.SUB_DELAY))
        return sub_messages_per_conn
