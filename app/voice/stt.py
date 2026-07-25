from app.core.settings import settings
from app.voice.errors import VoiceDependencyMissing


class SpeechToText:
    """
    Local speech-to-text via `faster-whisper` (I-11) -- optional
    extra, not installed by default (`requirements-voice.txt`).
    Lazily loaded exactly like `EmbeddingModel` (I-08): importing this
    module or constructing a `SpeechToText` never loads the model or
    requires the dependency to be installed; only `transcribe()` does.
    """

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ):
        self._model_size = model_size or settings.VOICE_STT_MODEL_SIZE
        self._device = device or settings.VOICE_STT_DEVICE
        self._compute_type = compute_type or settings.VOICE_STT_COMPUTE_TYPE
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise VoiceDependencyMissing(
                    "Speech-to-text requires the optional voice extra. "
                    "Install it with: pip install -r requirements-voice.txt"
                ) from exc

            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )

        return self._model

    def transcribe(self, audio, language: str | None = None) -> tuple[str, str | None]:
        """
        `audio` is a file path, file-like object, or numpy array --
        anything `faster_whisper.WhisperModel.transcribe` accepts.
        Returns `(text, detected_language)`. `detected_language` is
        Whisper's own audio-based detection -- a more reliable signal
        than running I-10's text-based `detect_language()` on a short
        transcript, and is what a `lair voice` round trip uses to pick
        the TTS reply's language.
        """

        model = self._ensure_loaded()
        segments, info = model.transcribe(audio, language=language)
        text = " ".join(segment.text.strip() for segment in segments).strip()

        return text, info.language


default_speech_to_text = SpeechToText()
