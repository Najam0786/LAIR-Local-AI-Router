from dataclasses import dataclass

import pytest

from app.voice.errors import VoiceDependencyMissing
from app.voice.stt import SpeechToText, default_speech_to_text


@dataclass
class _FakeSegment:
    text: str


@dataclass
class _FakeInfo:
    language: str


class _FakeWhisperModel:
    def __init__(self, segments: list[str], language: str):
        self._segments = [_FakeSegment(text=s) for s in segments]
        self._language = language

    def transcribe(self, audio, language=None):
        return self._segments, _FakeInfo(language=self._language)


class _FakeSpeechToText(SpeechToText):
    def __init__(self, segments: list[str], language: str):
        super().__init__()
        self._fake_model = _FakeWhisperModel(segments, language)

    def _ensure_loaded(self):
        return self._fake_model


def test_transcribe_joins_segments_and_returns_language():
    stt = _FakeSpeechToText([" hello ", "world "], "en")

    text, language = stt.transcribe("fake-audio")

    assert text == "hello world"
    assert language == "en"


def test_never_loads_model_on_construction():
    stt = SpeechToText()

    assert stt._model is None


def test_missing_dependency_raises_actionable_error():
    stt = SpeechToText()

    with pytest.raises(VoiceDependencyMissing, match="requirements-voice.txt"):
        stt.transcribe("fake-audio")
