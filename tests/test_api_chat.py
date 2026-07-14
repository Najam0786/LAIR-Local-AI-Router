import json

import app.api.chat as chat_api_module
from app.providers.stream_chunk import ProviderStreamChunk
from tests.conftest import FAKE_MODELS, FakeProvider


def _parse_sse_lines(text: str) -> list[dict | str]:
    events: list[dict | str] = []

    for line in text.splitlines():
        if not line.startswith("data: "):
            continue

        payload = line[len("data: ") :]
        events.append("[DONE]" if payload == "[DONE]" else json.loads(payload))

    return events


def _assemble_content(events: list[dict | str]) -> str:
    return "".join(
        event["choices"][0]["delta"].get("content") or ""
        for event in events
        if isinstance(event, dict)
    )


def test_chat_completions_without_providers_returns_503(client, clean_registry):
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 503


def test_chat_completions_happy_path(client, registered_fake_provider):
    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "please debug this python function"},
            ]
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["model"] == "qwen2.5-coder-32b"
    assert body["choices"][0]["message"]["content"] == "ok"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["usage"]["completion_tokens"] == 8


def test_chat_completions_accepts_content_as_list_of_parts(
    client, registered_fake_provider
):
    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "please debug this python"}
                    ],
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "qwen2.5-coder-32b"


def test_chat_completions_streams_happy_path_assembles_full_text(
    client, clean_registry
):
    model = FAKE_MODELS[1]  # qwen2.5-coder-32b
    provider = FakeProvider(
        [model],
        stream_chunks={
            model.id: [
                ProviderStreamChunk(delta="Hello"),
                ProviderStreamChunk(
                    delta=" world",
                    finish_reason="stop",
                    completion_tokens=2,
                    prompt_tokens=5,
                ),
            ]
        },
    )
    clean_registry.register(provider)

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "please debug this python"}],
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        events = _parse_sse_lines(response.read().decode())

    assert events[-1] == "[DONE]"
    assert _assemble_content(events) == "Hello world"


def test_chat_completions_stream_provider_failure_terminates_cleanly(
    client, clean_registry
):
    model = FAKE_MODELS[1]
    provider = FakeProvider([model], stream_failures={model.id})
    clean_registry.register(provider)

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "please debug this python"}],
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        events = _parse_sse_lines(response.read().decode())

    assert events[-1] == "[DONE]"
    assert "[LAIR error:" in _assemble_content(events)


def test_chat_completions_stream_persists_decision_execution_outcome(
    client, clean_registry
):
    model = FAKE_MODELS[1]
    provider = FakeProvider(
        [model],
        stream_chunks={
            model.id: [
                ProviderStreamChunk(
                    delta="Hello world",
                    finish_reason="stop",
                    completion_tokens=2,
                    prompt_tokens=5,
                ),
            ]
        },
    )
    clean_registry.register(provider)

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "please debug this python"}],
            "stream": True,
        },
    ) as response:
        response.read()

    records = chat_api_module.default_decision_repository.all()

    assert records[-1].execution_outcome is not None
    assert records[-1].execution_outcome.success is True
    assert records[-1].execution_outcome.completion_tokens == 2


def test_chat_completions_stream_failure_persists_failed_outcome(
    client, clean_registry
):
    model = FAKE_MODELS[1]
    provider = FakeProvider([model], stream_failures={model.id})
    clean_registry.register(provider)

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "please debug this python"}],
            "stream": True,
        },
    ) as response:
        response.read()

    records = chat_api_module.default_decision_repository.all()

    assert records[-1].execution_outcome is not None
    assert records[-1].execution_outcome.success is False
    assert "simulated stream failure" in records[-1].execution_outcome.error


def test_chat_completions_routes_even_when_no_model_has_the_requested_capability(
    client, registered_fake_provider
):
    # Capability matching is a soft scoring preference, not a hard filter --
    # a request for a capability no registered model has still routes to
    # the best-available candidate rather than 404ing.
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "translate this to french"}]},
    )

    assert response.status_code == 200


def test_chat_completions_provider_failure_returns_502_and_persists_outcome(
    client, clean_registry
):
    model = FAKE_MODELS[1]  # qwen2.5-coder-32b
    provider = FakeProvider([model], failures={model.id})
    clean_registry.register(provider)

    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "please debug this python"}]},
    )

    assert response.status_code == 502

    records = chat_api_module.default_decision_repository.all()

    assert records[-1].execution_outcome is not None
    assert records[-1].execution_outcome.success is False


def test_openai_models_endpoint_lists_registered_models(client, registered_fake_provider):
    response = client.get("/v1/models")

    assert response.status_code == 200

    body = response.json()

    assert body["object"] == "list"
    ids = {entry["id"] for entry in body["data"]}
    assert "qwen2.5-coder-32b" in ids
