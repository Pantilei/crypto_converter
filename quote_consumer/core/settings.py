import logging
import sys

from loguru import logger
from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradesToCandleProcessorConfigs(BaseModel):
    flush_to_db_period: int = 30  # Flush candles every 30 second to DB
    buffer_interval: int = 60  # Buffer candles are stored maximum for 60 seconds
    buffer_clean_period: int = 45  # Clean in memory buffer every 45 seconds
    storage_max_interval: int = 7  # Maximum time period of candles in days
    storage_clean_period: int = 600  # Clean every 10 minutes old candles from DB


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="UTF-8", extra="ignore"
    )

    DEBUG: bool = True
    DB_SERVICE: PostgresDsn
    APP_PORT: int = Field(9001, validation_alias="QUOTE_CONSUMER_APP_PORT")
    FLUSH_TO_DB_PERIOD: int = 30
    TRADES_TO_CANDLES_CONFIG: TradesToCandleProcessorConfigs = TradesToCandleProcessorConfigs()


settings = Settings()  # type: ignore

logger.configure(handlers=[{"sink": sys.stderr, "level": logging.DEBUG if settings.DEBUG else logging.INFO}])
