import uvicorn
from fastapi import FastAPI

from quote_consumer.api.api import router as api
from quote_consumer.core.events import LifeSpan
from quote_consumer.core.settings import settings

app = FastAPI(debug=settings.DEBUG, lifespan=LifeSpan)

app.include_router(api)


@app.get("/health", tags=["system"], include_in_schema=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# TODO: Replace with the gRPC server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
