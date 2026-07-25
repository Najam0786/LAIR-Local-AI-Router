from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.
    """

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    APP_NAME: str = "LAIR"
    APP_VERSION: str = "0.3.0-alpha"

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

    ENABLE_COMPLEXITY_TRIAGE: bool = True

    # I-04 Phase 2. Off by default and unconfigured -- an uncached call
    # is a real inference round-trip, unlike the zero-cost Phase 1 rules.
    ENABLE_MODEL_ASSISTED_COMPLEXITY: bool = False

    COMPLEXITY_CLASSIFIER_MODEL_ID: str = ""

    COMPLEXITY_CLASSIFICATION_CACHE_TTL_SECONDS: int = 3600

    # I-09. Safe to default on: with no summarizer model configured,
    # compression falls back to plain truncation (no inference cost).
    ENABLE_CONTEXT_COMPRESSION: bool = True

    CONTEXT_COMPRESSION_THRESHOLD: float = 0.8

    CONTEXT_COMPRESSION_KEEP_RECENT_TURNS: int = 6

    CONTEXT_COMPRESSION_SUMMARIZER_MODEL_ID: str = ""

    ENABLE_LANGUAGE_ROUTING: bool = True

    # I-15. Safe to default on: a no-op scoring bias with no behavior
    # change at all on a desktop (psutil reports no battery there).
    ENABLE_BATTERY_AWARENESS: bool = True

    # ------------------------------------------------------------------
    # Streaming-Aware Routing (I-16, ADR-0021)
    #
    # Off by default: surfaces "slow but possible" picks that
    # otherwise wouldn't be candidates at all, and no execution backend
    # in this codebase actually runs a model via SSD streaming yet
    # (LM Studio doesn't expose mmap/streaming knobs) -- an opt-in
    # signal until a real streaming-capable provider exists.
    # ------------------------------------------------------------------

    ENABLE_STREAMING_ROUTING: bool = False

    STREAMING_MIN_VIABILITY: float = 0.5

    # Heuristic proxy for "how much slower than fitting in RAM this
    # would be" (needed-vs-available memory ratio) -- not a measured
    # figure; see ModelScorer's streaming_penalty factor.
    STREAMING_MAX_LATENCY_MULTIPLIER: float = 8.0

    # Conservative default per I-07's design notes: off until a user
    # opts in, given a stale cached answer is a real correctness risk.
    ENABLE_RESPONSE_CACHE: bool = False

    RESPONSE_CACHE_TTL_SECONDS: int = 3600

    RESPONSE_CACHE_MAX_ENTRIES: int = 500

    # ------------------------------------------------------------------
    # Hybrid Cloud Escalation (I-06, RFC-0001)
    #
    # Off by default. CLAUDE.md constraint #1: never send a prompt to
    # any cloud API unless this is explicitly enabled AND a nonzero
    # budget is configured -- both conditions, always.
    # ------------------------------------------------------------------

    ENABLE_CLOUD_ESCALATION: bool = False

    CLOUD_MONTHLY_BUDGET_USD: float = 0.0

    CLOUD_PROVIDER_API_KEY: str = ""

    CLOUD_PROVIDER_BASE_URL: str = "https://api.openai.com/v1"

    CLOUD_PROVIDER_MODEL_ID: str = "gpt-4o-mini"

    CLOUD_PROVIDER_INPUT_PRICE_PER_1M_USD: float = 5.00

    CLOUD_PROVIDER_OUTPUT_PRICE_PER_1M_USD: float = 15.00

    # A request only escalates when complexity is at/above this AND
    # the local decision's confidence is below
    # CLOUD_ESCALATION_LOCAL_CONFIDENCE_THRESHOLD -- both signals
    # together, not complexity alone (RFC-0001's stated risk mitigation).
    CLOUD_ESCALATION_COMPLEXITY_THRESHOLD: int = 5

    CLOUD_ESCALATION_LOCAL_CONFIDENCE_THRESHOLD: float = 0.3

    # ------------------------------------------------------------------
    # RAG-Lite Document Pipeline (I-08)
    #
    # Local embedding model + chunking; no external vector DB. All
    # processing local -- the embedding model is fetched once from
    # Hugging Face Hub on first use, the same one-time-acquisition
    # pattern as an LM Studio model download, never per-request.
    # ------------------------------------------------------------------

    RAG_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    RAG_CHUNK_SIZE_TOKENS: int = 300

    RAG_CHUNK_OVERLAP_TOKENS: int = 50

    RAG_RETRIEVAL_TOP_K: int = 5

    RAG_RETRIEVAL_TOKEN_BUDGET: int = 1500

    # ------------------------------------------------------------------
    # Persistent Project Memory (I-18, RFC-0002, ADR-0020)
    #
    # Off by default: the most privacy-sensitive feature LAIR has --
    # durable storage of conversation content -- must be an explicit
    # choice, never a silent default (CLAUDE.md local-first posture).
    # ------------------------------------------------------------------

    ENABLE_PROJECT_MEMORY: bool = False

    MEMORY_DEDUP_SIMILARITY_THRESHOLD: float = 0.92

    MEMORY_RETRIEVAL_TOP_K: int = 5

    MEMORY_TOKEN_BUDGET: int = 500

    # ------------------------------------------------------------------
    # Voice Interface (I-11)
    #
    # Optional extra (`pip install -r requirements-voice.txt`), not
    # installed by default. Endpoints degrade to a 503 with an
    # actionable message when the dependency (or, for TTS, the model
    # files) isn't present -- never a crash.
    # ------------------------------------------------------------------

    VOICE_STT_MODEL_SIZE: str = "base"

    VOICE_STT_DEVICE: str = "cpu"

    VOICE_STT_COMPUTE_TYPE: str = "int8"

    VOICE_TTS_MODEL_PATH: str = ""

    VOICE_TTS_VOICES_PATH: str = ""

    VOICE_TTS_DEFAULT_VOICE: str = "af_sarah"

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