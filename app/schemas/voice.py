from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """OpenAI-compatible `/v1/audio/transcriptions` response shape."""

    text: str
    language: str | None = None


class SpeechRequest(BaseModel):
    """OpenAI-compatible `/v1/audio/speech` request shape."""

    input: str
    voice: str | None = Field(default=None)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    lang: str | None = Field(
        default=None,
        description="Kokoro locale code (e.g. 'en-us', 'es'). Not part "
        "of the OpenAI schema; omit to use Settings.VOICE_TTS_DEFAULT_VOICE's "
        "implied language.",
    )
