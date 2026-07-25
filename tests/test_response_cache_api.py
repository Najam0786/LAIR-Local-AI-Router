from app.core.settings import settings


def _request(**overrides):
    body = {
        "messages": [
            {"role": "user", "content": "please debug this python function"}
        ]
    }
    body.update(overrides)
    return body


def test_cache_disabled_by_default_never_hits(client, registered_fake_provider):
    first = client.post("/v1/chat/completions", json=_request())
    second = client.post("/v1/chat/completions", json=_request())

    assert first.json()["lair_meta"]["cache_hit"] is False
    assert second.json()["lair_meta"]["cache_hit"] is False


def test_second_identical_request_is_served_from_cache(
    client, registered_fake_provider, monkeypatch
):
    monkeypatch.setattr(settings, "ENABLE_RESPONSE_CACHE", True)

    first = client.post("/v1/chat/completions", json=_request())
    second = client.post("/v1/chat/completions", json=_request())

    assert first.json()["lair_meta"]["cache_hit"] is False
    assert second.json()["lair_meta"]["cache_hit"] is True
    assert second.json()["choices"][0]["message"]["content"] == (
        first.json()["choices"][0]["message"]["content"]
    )
    # No real inference happened on the hit -- no savings claim is made.
    assert second.json()["lair_meta"]["estimated_savings_usd"] is None


def test_different_conversation_history_is_not_a_cache_hit(
    client, registered_fake_provider, monkeypatch
):
    monkeypatch.setattr(settings, "ENABLE_RESPONSE_CACHE", True)

    client.post("/v1/chat/completions", json=_request())
    different = client.post(
        "/v1/chat/completions",
        json=_request(
            messages=[
                {"role": "system", "content": "different system prompt"},
                {
                    "role": "user",
                    "content": "please debug this python function",
                },
            ]
        ),
    )

    assert different.json()["lair_meta"]["cache_hit"] is False


def test_per_request_opt_out_bypasses_cache(
    client, registered_fake_provider, monkeypatch
):
    monkeypatch.setattr(settings, "ENABLE_RESPONSE_CACHE", True)

    client.post("/v1/chat/completions", json=_request())
    second = client.post(
        "/v1/chat/completions", json=_request(lair_no_cache=True)
    )

    assert second.json()["lair_meta"]["cache_hit"] is False


def test_streaming_requests_are_never_cached(
    client, registered_fake_provider, monkeypatch
):
    monkeypatch.setattr(settings, "ENABLE_RESPONSE_CACHE", True)

    client.post("/v1/chat/completions", json=_request())

    with client.stream(
        "POST", "/v1/chat/completions", json=_request(stream=True)
    ) as response:
        response.read()

    second = client.post("/v1/chat/completions", json=_request())
    assert second.json()["lair_meta"]["cache_hit"] is True
