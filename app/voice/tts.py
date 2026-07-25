import io
import struct
import wave

import numpy as np

from app.core.settings import settings
from app.voice.errors import VoiceDependencyMissing


def _pcm16_wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    """
    Encodes float32 samples in [-1, 1] (Kokoro's output shape) as a
    16-bit PCM mono WAV file, via the stdlib `wave` module -- no extra
    dependency needed just to package audio for an HTTP response.
    """

    clipped = np.clip(samples, -1.0, 1.0)
    pcm16 = (clipped * 32767.0).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack(f"<{len(pcm16)}h", *pcm16))

    return buffer.getvalue()


class TextToSpeech:
    """
    Local text-to-speech via `kokoro-onnx` (I-11) -- optional extra,
    not installed by default. Unlike `EmbeddingModel`/`SpeechToText`,
    Kokoro does not auto-download its weights from a hub on first use;
    it requires a local `model.onnx` and `voices.bin` (paths from
    `Settings.VOICE_TTS_MODEL_PATH`/`VOICE_TTS_VOICES_PATH`, downloaded
    once by the user from the kokoro-onnx releases page) -- a real
    difference from I-08's embedding model worth being honest about
    rather than pretending it's the same one-time-auto-fetch pattern.
    """

    def __init__(self, model_path: str | None = None, voices_path: str | None = None):
        self._model_path = model_path or settings.VOICE_TTS_MODEL_PATH
        self._voices_path = voices_path or settings.VOICE_TTS_VOICES_PATH
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            if not self._model_path or not self._voices_path:
                raise VoiceDependencyMissing(
                    "Text-to-speech requires Settings.VOICE_TTS_MODEL_PATH "
                    "and VOICE_TTS_VOICES_PATH, pointing at a local "
                    "kokoro-onnx model.onnx/voices.bin pair (downloaded "
                    "once from the kokoro-onnx releases page)."
                )

            try:
                from kokoro_onnx import Kokoro
            except ImportError as exc:
                raise VoiceDependencyMissing(
                    "Text-to-speech requires the optional voice extra. "
                    "Install it with: pip install -r requirements-voice.txt"
                ) from exc

            self._model = Kokoro(self._model_path, self._voices_path)

        return self._model

    def synthesize_wav_bytes(
        self,
        text: str,
        voice: str | None = None,
        lang: str | None = None,
        speed: float = 1.0,
    ) -> bytes:
        model = self._ensure_loaded()
        samples, sample_rate = model.create(
            text,
            voice=voice or settings.VOICE_TTS_DEFAULT_VOICE,
            speed=speed,
            lang=lang or "en-us",
        )

        return _pcm16_wav_bytes(samples, sample_rate)


default_text_to_speech = TextToSpeech()
