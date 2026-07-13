from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "LAIR"
    APP_VERSION: str = "0.1.0"

    LM_STUDIO_URL: str = "http://localhost:1234/v1"

    DEFAULT_MODEL: str = ""

    REQUEST_TIMEOUT: int = 300

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()