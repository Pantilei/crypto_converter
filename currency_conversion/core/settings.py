from pydantic import Field, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="UTF-8", extra="ignore")

    DEBUG: bool = True
    DB_SERVICE: PostgresDsn
    ALLOWED_ORIGINS: list[str]
    APP_PORT: int = Field(9000, validation_alias="CURRENCY_CONVERSION_APP_PORT")
    QUOTE_CONSUMER_SERVICE: HttpUrl = HttpUrl("http://localhost:9005")


settings = Settings()  # type: ignore
