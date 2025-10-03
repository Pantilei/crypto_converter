

from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from schemas.types import Ticker


class CandleDB(TypedDict):
    ticker: Ticker
    t: datetime
    open: Decimal
    close: Decimal
    high: Decimal
    low: Decimal
    volume: Decimal
