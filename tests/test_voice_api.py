import app.api.voice as voice_api_module
from app.voice.errors import VoiceDependencyMissing


class _StubSpeechToText:
    def transcribe(self, audio, language=None):
        return "hello from audio", "en"


class _FailingSpeechToText:
    def transcribe(self, audio, language=None):
        raise VoiceDependencyMissing("voice extra not installed")


class _StubTextToSpeech:
    def synthesize_wav_bytes(self, text, voice=None, lang=None, speed=1.0):
        return b"RIFF-fake-wav-bytes"


class _FailingTextToSpeech:
    def synthesize_wav_bytes(self, text, voice=None, lang=None, speed=1.0):
        raise VoiceDependencyMissing("voice extra not installed")


def test_transcription_endpoint_returns_text_and_language(client, monkeypatch):
    monkeypatch.setattr(voice_api_module, "default_speech_to_text", _StubSpeechToText())

    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("audio.wav", b"fake-audio-bytes")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "hello from audio", "language": "en"}


def test_transcription_endpoint_returns_503_when_dependency_missing(client, monkeypatch):
    monkeypatch.setattr(voice_api_module, "default_speech_to_text", _FailingSpeechToText())

    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("audio.wav", b"fake-audio-bytes")},
    )

    assert response.status_code == 503
    assert "voice extra" in response.json()["detail"]


def test_speech_endpoint_returns_wav_audio(client, monkeypatch):
    monkeypatch.setattr(voice_api_module, "default_text_to_speech", _StubTextToSpeech())

    response = client.post("/v1/audio/speech", json={"input": "hello"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"RIFF-fake-wav-bytes"


def test_speech_endpoint_returns_503_when_dependency_missing(client, monkeypatch):
    monkeypatch.setattr(voice_api_module, "default_text_to_speech", _FailingTextToSpeech())

    response = client.post("/v1/audio/speech", json={"input": "hello"})

    assert response.status_code == 503
    assert "voice extra" in response.json()["detail"]


def test_real_speech_to_text_degrades_gracefully_without_the_optional_extra(client):
    """
    Not mocked: exercises the real `SpeechToText` path in an
    environment where the voice extra's runtime dependencies genuinely
    aren't installed (this test venv never installs
    requirements-voice.txt) -- proves the 503 path works end-to-end,
    not just that the wrapper's exception type is right.
    """

    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("audio.wav", b"fake-audio-bytes")},
    )

    assert response.status_code == 503
