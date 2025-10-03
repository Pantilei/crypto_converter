
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, Self, TypedDict

from pydantic import BaseModel, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

type Symbol = str

class Ticker(str):
    """Ticker is composed from symbol and exchange. Ex: BTCUSDT.BINANCE"""

    @property
    def symbol(self) -> str:
        return self.split(".")[0]

    @property
    def exchange(self) -> str:
        return self.split(".")[1]
    
    @classmethod
    def build(cls, symbol: Symbol, exchange: str) -> Self:
        return cls(f"{symbol}.{exchange}")
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source, handler: GetCoreSchemaHandler
    ) -> core_schema.AfterValidatorFunctionSchema:
        return core_schema.no_info_after_validator_function(
            cls, core_schema.str_schema()
        )
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema.update({
            "title": "Ticker",
            "type": "string",
            "example": "BTCUSDT.BINANCE",
            "description": "Unique identifier for symbol in exchange"
        })
        return json_schema


class Timestamp(int):

    @classmethod
    def from_dt(cls, dt: datetime) -> Self:
        return cls(dt.timestamp())

    def to_dt(self) -> datetime:
        return datetime.fromtimestamp(self, tz=UTC)

    @classmethod
    def now(cls) -> Self:
        return cls(datetime.now(tz=UTC).timestamp())

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.AfterValidatorFunctionSchema:
        return core_schema.no_info_after_validator_function(
            cls, core_schema.int_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema.update({
            "title": "Timestamp",
            "type": "integer",
            "example": 1728028800,  # Example: 2024-10-04T00:00:00Z
            "description": "Unix timestamp in seconds (UTC)."
        })
        return json_schema



class Candle(BaseModel):
    T: Ticker
    t: datetime
    o: Decimal
    c: Decimal
    l: Decimal
    h: Decimal
    v: Decimal

    def update(self, trade: "Trade") -> None:
        self.v += trade.v
        self.c = trade.p
        self.l = min(self.l, trade.p)
        self.h = max(self.h, trade.p)


class Trade(BaseModel):
    t: int  # in milliseconds
    T: Ticker
    p: Decimal
    v: Decimal

    def to_candle(self) -> Candle:
        t = datetime.fromtimestamp(self.t // 1000, tz=UTC)
        return Candle(
            T=self.T, t=t, o=self.p, c=self.p, h=self.p, l=self.p, v=self.v
        )