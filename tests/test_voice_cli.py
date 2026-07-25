import json

import httpx

from lair.commands import voice as voice_command


def _mock_client(recorded: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/audio/transcriptions":
            recorded["transcription_request"] = request
            return httpx.Response(200, json={"text": "what's the weather", "language": "en"})

        if request.url.path == "/v1/chat/completions":
            recorded["chat_request"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-1",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "fake-model",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "it's sunny"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            )

        if request.url.path == "/v1/audio/speech":
            recorded["speech_request"] = json.loads(request.content)
            return httpx.Response(200, content=b"fake-wav-bytes")

        raise AssertionError(f"unexpected request to {request.url.path}")

    return httpx.Client(base_url="http://testserver", transport=httpx.MockTransport(handler))


def test_voice_round_trip_writes_reply_audio(tmp_path):
    input_path = tmp_path / "in.wav"
    input_path.write_bytes(b"fake-input-audio")
    output_path = tmp_path / "out.wav"
    recorded = {}

    reply_text = voice_command.run(
        str(input_path),
        str(output_path),
        client=_mock_client(recorded),
    )

    assert reply_text == "it's sunny"
    assert output_path.read_bytes() == b"fake-wav-bytes"
    assert recorded["chat_request"]["messages"][0]["content"] == "what's the weather"
    assert recorded["speech_request"]["lang"] == "en-us"


def test_voice_round_trip_forwards_project_scope(tmp_path):
    input_path = tmp_path / "in.wav"
    input_path.write_bytes(b"fake-input-audio")
    output_path = tmp_path / "out.wav"
    recorded = {}

    voice_command.run(
        str(input_path),
        str(output_path),
        project_scope="my-project",
        client=_mock_client(recorded),
    )

    assert recorded["chat_request"]["lair_project_scope"] == "my-project"
