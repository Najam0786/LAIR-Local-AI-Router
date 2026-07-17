from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.
    """

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    APP_NAME: str = "LAIR"
    APP_VERSION: str = "0.2.0-alpha"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DEBUG: bool = False

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------

    DEFAULT_PROVIDER: str = "lmstudio"

    LM_STUDIO_URL: str = "http://localhost:1234/v1"

    OLLAMA_URL: str = "http://localhost:11434"

    ENABLE_LM_STUDIO_AUTOSTART: bool = True

    LMS_CLI_PATH: str = "lms"

    LMS_PROBE_TIMEOUT_SECONDS: int = 3

    LMS_RECOVERY_TIMEOUT_SECONDS: int = 60

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    DEFAULT_MODEL: str = ""

    REQUEST_TIMEOUT: int = 300

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    ENABLE_CAPABILITY_ROUTING: bool = True

    ENABLE_EXPLAINABILITY: bool = True

    ENABLE_BENCHMARKS: bool = True

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()