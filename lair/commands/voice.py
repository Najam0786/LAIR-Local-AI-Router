from pathlib import Path

import httpx

from app.voice.language_map import whisper_to_kokoro_lang


def run(
    input_path: str,
    output_path: str,
    base_url: str = "http://127.0.0.1:8000",
    project_scope: str | None = None,
    client: httpx.Client | None = None,
) -> str:
    """
    File-based voice round trip (I-11): transcribes `input_path`,
    routes the transcript through LAIR's normal `/v1/chat/completions`
    (so I-10 language routing, I-18 project memory, etc. all apply
    unchanged), then synthesizes the reply to `output_path`.

    Deliberately file-based, not a live microphone loop -- real-time
    audio capture/playback needs a system audio dependency this pass
    doesn't introduce (mirrors the plan's own "later a minimal web UI"
    phasing for the richer interaction modes).

    Accepts an injected `client` (e.g. backed by `httpx.MockTransport`)
    for testing without a real running server.
    """

    audio_bytes = Path(input_path).read_bytes()
    owns_client = client is None
    client = client or httpx.Client(base_url=base_url, timeout=120.0)

    try:
        transcription = client.post(
            "/v1/audio/transcriptions",
            files={"file": (Path(input_path).name, audio_bytes)},
        )
        transcription.raise_for_status()
        transcription_data = transcription.json()
        text = transcription_data["text"]
        detected_language = transcription_data.get("language")

        payload = {"messages": [{"role": "user", "content": text}]}
        if project_scope:
            payload["lair_project_scope"] = project_scope

        chat_response = client.post("/v1/chat/completions", json=payload)
        chat_response.raise_for_status()
        reply_text = chat_response.json()["choices"][0]["message"]["content"]

        speech = client.post(
            "/v1/audio/speech",
            json={
                "input": reply_text,
                "lang": whisper_to_kokoro_lang(detected_language),
            },
        )
        speech.raise_for_status()

        Path(output_path).write_bytes(speech.content)

        return reply_text
    finally:
        if owns_client:
            client.close()
