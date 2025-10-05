import asyncio
from asyncio import Queue
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar, get_args

from aiosonic.web_socket_client import WebSocketClient, WebSocketConnection
from loguru import logger
from pydantic import BaseModel, ValidationError

from schemas.types import Trade


class BaseTradePayload(BaseModel):
    def to_trade(self) -> Trade:  # type: ignore
        """Transform provider trade into internal structure."""


class RTTradesProvider[T: BaseTradePayload]:
    """Base class for Real Time Trades Provider"""

    if TYPE_CHECKING:
        __payload_type__: type[T]
        ws_url: ClassVar[str]

    __ws_client__: ClassVar[WebSocketClient] = WebSocketClient()
    __trade_providers__: ClassVar[list[type["RTTradesProvider"]]] = []
    __trades_queue__: ClassVar[Queue[Trade]] = Queue(maxsize=1_000)
    _connection_retry_period: ClassVar[int] = 10

    def __init__(self) -> None:
        self._connections: list[WebSocketConnection] = []
        self._listeners: list[asyncio.Task[None]] = []

    def __init_subclass__(cls) -> None:
        if getattr(cls, "ws_url", None) is None:
            raise RuntimeError(f"{cls.__name__} must have ws_url defined.")

        RTTradesProvider.__trade_providers__.append(cls)
        for org in cls.__orig_bases__:  #type: ignore
            cls.__payload_type__ = get_args(org)[0]

    @property
    def trades_queue(self) -> Queue[Trade]:
        return self.__trades_queue__

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for trades_provider in self.__trade_providers__:
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
            await self._connect_and_listen(sub_msgs, delay)

    async def stop(self) -> None:
        for listener in self._listeners:
            listener.cancel()

        for conn in self._connections:
            if conn.connected:
                await conn.close()

    async def _connect_and_listen(
        self,
        sub_msgs: list[dict[str, Any]],
        sub_msg_delay: float | None = None
    ) -> None:
        logger.info(f"New connection to WS: {self.ws_url}")
        conn = await self.__ws_client__.connect(self.ws_url)
        self._connections.append(conn)
        listener = asyncio.create_task(self._listen(conn, sub_msgs, sub_msg_delay=sub_msg_delay))
        self._listeners.append(listener)

        def __retry_callback(fut: asyncio.Future[None]) -> None:
            if fut.cancelled():
                return
            if ex := fut.exception():
                logger.critical(f"Error on listening: {ex}")
                return
            self._connections = [c for c in self._connections if c is not conn]
            self._listeners.remove(listener)
            asyncio.get_running_loop().call_later(
                self._connection_retry_period,
                lambda s_msgs=sub_msgs: asyncio.create_task(self._connect_and_listen(s_msgs))  # type: ignore
            )

        listener.add_done_callback(__retry_callback)

    async def _listen(
        self,
        conn: WebSocketConnection,
        sub_message: list[dict[str,  Any]],
        sub_msg_delay: float | None = None
    ) -> None:
        for sm in sub_message:
            await conn.send_json(sm)
            # If provider has restriction on rate of subscription message. Ex: Binance has 5 msg/sec
            if sub_msg_delay:
                await asyncio.sleep(sub_msg_delay)

        # Loop will finish in case of server disconnect
        async for msg in conn:
            try:
                payload: T = self.__payload_type__.model_validate_json(msg.data)
            except ValidationError:
                logger.debug(f"Non trade message: {msg.data}")
                continue
            await self.__trades_queue__.put(payload.to_trade())
