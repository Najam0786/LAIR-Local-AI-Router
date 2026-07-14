import app.api.chat as chat_api_module


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


def test_chat_completions_rejects_streaming(client, registered_fake_provider):
    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "please debug this"}],
            "stream": True,
        },
    )

    assert response.status_code == 400


def test_chat_completions_returns_404_when_no_model_matches(
    client, registered_fake_provider
):
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "translate this to french"}]},
    )

    assert response.status_code == 404


def test_chat_completions_provider_failure_returns_502_and_persists_outcome(
    client, clean_registry
):
    from tests.conftest import FAKE_MODELS, FakeProvider

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
