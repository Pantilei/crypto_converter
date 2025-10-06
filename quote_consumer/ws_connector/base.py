import asyncio
import traceback
from asyncio import Queue
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar, get_args

import ujson
from loguru import logger
from pydantic import BaseModel, ValidationError
from websockets import ClientConnection, ConnectionClosedError, ConnectionClosedOK
from websockets.asyncio.client import connect

from schemas.types import Trade


class BaseTradePayload(BaseModel):
    def to_trade(self) -> Trade:  # type: ignore
        """Transform provider trade into internal structure."""


class RTTradesProvider[T: BaseTradePayload]:
    """Base class for Real Time Trades Provider"""

    if TYPE_CHECKING:
        __payload_type__: type[T]
        ws_url: ClassVar[str]

    __trade_providers__: ClassVar[list[type["RTTradesProvider"]]] = []
    __trades_queue__: ClassVar[Queue[Trade]] = Queue(maxsize=1_000)
    __connections__: ClassVar[set[ClientConnection]] = set()
    __listeners__: ClassVar[list[asyncio.Task[None]]] = []

    def __init_subclass__(cls) -> None:
        if getattr(cls, "ws_url", None) is None:
            raise RuntimeError(f"{cls.__name__} must have ws_url defined.")

        RTTradesProvider.__trade_providers__.append(cls)
        for org in cls.__orig_bases__:  #type: ignore
            cls.__payload_type__ = get_args(org)[0]

    @classmethod
    def get_trade_queue(cls) -> Queue[Trade]:
        return cls.__trades_queue__

    @classmethod
    async def run(cls) -> None:
        async with asyncio.TaskGroup() as tg:
            for trades_provider in cls.__trade_providers__:
                logger.info(f"Starting to listen for trades of {trades_provider.__name__}")
                tg.create_task(trades_provider().robust_listen())

    async def get_conn_sub_message(self) -> Iterable[tuple[list[dict[str, Any]], float | None]]:
        """
        Generate subscription messages.
        Number of items in returned iterable will define the number of connections
        """
        return []

    async def robust_listen(self) -> None:
        for sub_msgs, delay in await self.get_conn_sub_message():
            listener = asyncio.create_task(self._connect_and_listen(sub_msgs, delay))
            RTTradesProvider.__listeners__.append(listener)
            await asyncio.sleep(5 * (delay or 0.2))  # Add some delay between creating the connection from same IP

    @classmethod
    async def stop(cls) -> None:
        for listener in cls.__listeners__:
            listener.cancel()

        for conn in cls.__connections__:
            logger.info(f"Closed WS connection: {conn.id}")
            await conn.close()

    async def _connect_and_listen(
        self, sub_msgs: list[dict[str, Any]], sub_msg_delay: float | None = None
    ) -> None:
        # NOTE: There is a build in exponential backoff
        async for conn in connect(self.ws_url):
            logger.info(f"WS connection: {conn.id}")
            RTTradesProvider.__connections__.add(conn)
            try:
                await self._listen(conn, sub_msgs, sub_msg_delay)
            except ConnectionClosedOK:
                logger.info("Controlled close of WS connection")
                break
            except ConnectionClosedError:
                logger.info("WS Connection lost")
            except Exception as ex:
                logger.error(f"Critical error on listen: {ex}")
                logger.error(traceback.format_exc())
                break

            RTTradesProvider.__connections__.remove(conn)

    async def _listen(
        self,
        conn: ClientConnection,
        sub_message: list[dict[str,  Any]],
        sub_msg_delay: float | None = None
    ) -> None:
        for sm in sub_message:
            await conn.send(ujson.dumps(sm))
            # If provider has restriction on rate of subscription message. Ex: Binance has 5 msg/sec
            if sub_msg_delay:
                await asyncio.sleep(sub_msg_delay)

        # Loop will finish in case of server disconnect
        async for msg in conn:
            try:
                payload: T = self.__payload_type__.model_validate_json(msg)
            except ValidationError:
                logger.debug(f"Non trade message: {msg.decode() if isinstance(msg, bytes) else msg}")
                continue
            await self.__trades_queue__.put(payload.to_trade())
