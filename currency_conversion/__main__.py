import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from currency_conversion.api.api import router as api
from currency_conversion.core.events import LifeSpan
from currency_conversion.core.settings import settings

app = FastAPI(debug=settings.DEBUG, lifespan=LifeSpan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)

@app.get("/health", tags=["system"], include_in_schema=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
