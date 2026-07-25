import wave
import io

import numpy as np
import pytest

from app.voice.errors import VoiceDependencyMissing
from app.voice.tts import TextToSpeech, _pcm16_wav_bytes


class _FakeKokoro:
    def __init__(self, samples: np.ndarray, sample_rate: int):
        self._samples = samples
        self._sample_rate = sample_rate

    def create(self, text, voice, speed=1.0, lang="en-us"):
        return self._samples, self._sample_rate


class _FakeTextToSpeech(TextToSpeech):
    def __init__(self, samples: np.ndarray, sample_rate: int):
        super().__init__(model_path="fake.onnx", voices_path="fake.bin")
        self._fake_model = _FakeKokoro(samples, sample_rate)

    def _ensure_loaded(self):
        return self._fake_model


def test_pcm16_wav_bytes_round_trips_through_wave_module():
    samples = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)

    wav_bytes = _pcm16_wav_bytes(samples, sample_rate=24000)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 24000
        assert wav_file.getnframes() == len(samples)


def test_synthesize_wav_bytes_produces_a_valid_wav():
    samples = np.zeros(100, dtype=np.float32)
    tts = _FakeTextToSpeech(samples, sample_rate=24000)

    wav_bytes = tts.synthesize_wav_bytes("hello world")

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getframerate() == 24000
        assert wav_file.getnframes() == 100


def test_never_loads_model_on_construction():
    tts = TextToSpeech(model_path="a", voices_path="b")

    assert tts._model is None


def test_missing_config_raises_actionable_error():
    tts = TextToSpeech(model_path="", voices_path="")

    with pytest.raises(VoiceDependencyMissing, match="VOICE_TTS_MODEL_PATH"):
        tts.synthesize_wav_bytes("hello")
