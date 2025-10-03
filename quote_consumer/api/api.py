

from fastapi import APIRouter

from quote_consumer.api.candles import router as candles_router

router = APIRouter()

router.include_router(candles_router, prefix="/candles")
