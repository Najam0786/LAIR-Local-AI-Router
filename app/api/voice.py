import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.schemas.voice import SpeechRequest, TranscriptionResponse
from app.voice.errors import VoiceDependencyMissing
from app.voice.stt import default_speech_to_text
from app.voice.tts import default_text_to_speech

router = APIRouter(tags=["Voice"])


@router.post("/v1/audio/transcriptions", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = None,
) -> TranscriptionResponse:
    """
    OpenAI-compatible speech-to-text (I-11). Requires the optional
    voice extra (`pip install -r requirements-voice.txt`); returns 503
    with an actionable message when it isn't installed, rather than a
    generic 500.
    """

    raw = await file.read()

    try:
        text, detected_language = default_speech_to_text.transcribe(
            io.BytesIO(raw), language=language
        )
    except VoiceDependencyMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return TranscriptionResponse(text=text, language=detected_language)


@router.post("/v1/audio/speech")
async def synthesize_speech(request: SpeechRequest) -> Response:
    """
    OpenAI-compatible text-to-speech (I-11), returning a WAV file.
    Requires `Settings.VOICE_TTS_MODEL_PATH`/`VOICE_TTS_VOICES_PATH`
    (a local kokoro-onnx model, downloaded once by the user -- Kokoro
    does not auto-fetch weights the way I-08's embedding model does)
    in addition to the optional voice extra; 503 with an actionable
    message when either is missing.
    """

    try:
        wav_bytes = default_text_to_speech.synthesize_wav_bytes(
            request.input,
            voice=request.voice,
            lang=request.lang,
            speed=request.speed,
        )
    except VoiceDependencyMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return Response(content=wav_bytes, media_type="audio/wav")
