

from fastapi import APIRouter

from currency_conversion.api.quote import router as quote_router

router = APIRouter()

router.include_router(quote_router, prefix="/convert", tags=["quote"])
