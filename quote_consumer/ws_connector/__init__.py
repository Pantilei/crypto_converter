"""
Perform monkey patching of of aiosonic.WebSocketConnection._frame_dispatch_loop
OPCODE_PING is not handled, which is required by binance api
"""

import asyncio

from aiosonic.web_socket_client import Message, MessageType, WebSocketConnection

from quote_consumer.ws_connector.base import RTTradesProvider
from quote_consumer.ws_connector.binance import BinanceRTTradesProvider

__all__ = [
    "BinanceRTTradesProvider",
    "RTTradesProvider",
]

async def _patched_frame_dispatch_loop(self: WebSocketConnection) -> None:
    try:
        while self.connected:
            try:
                opcode, payload = await self._read_frame()
            except asyncio.IncompleteReadError:
                self.connected = False
                break

            if opcode == self.OPCODE_TEXT:
                msg = Message.create_text(payload.decode("utf-8"))
                await self._enqueue(self._msg_queue, msg)
            elif opcode == self.OPCODE_BINARY:
                msg = Message.create_binary(payload)
                await self._enqueue(self._msg_queue, msg)
            elif opcode == self.OPCODE_PONG:
                msg = Message(
                    type=MessageType.PONG,
                    data=payload,
                    raw_data=payload,
                    opcode=self.OPCODE_PONG,
                )
                await self._pong_queue.put(msg)
            elif opcode == self.OPCODE_CLOSE:
                self.connected = False
                break
            elif opcode == self.OPCODE_PING:
                await self._send_frame(self.OPCODE_PONG, payload)
    except Exception:
        self.connected = False

# Monkey patch
WebSocketConnection._frame_dispatch_loop = _patched_frame_dispatch_loop
