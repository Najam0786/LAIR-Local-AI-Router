import asyncio

from app.core.settings import settings
from app.providers.cloud import OpenAICompatibleCloudProvider


def test_list_models_empty_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "")
    provider = OpenAICompatibleCloudProvider()

    result = asyncio.run(provider.list_models())

    assert result == []


def test_list_models_returns_configured_model_with_key(monkeypatch):
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_MODEL_ID", "gpt-4o-mini")
    provider = OpenAICompatibleCloudProvider()

    result = asyncio.run(provider.list_models())

    assert len(result) == 1
    assert result[0].id == "gpt-4o-mini"
    assert result[0].provider == "cloud"


def test_health_check_false_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "")
    provider = OpenAICompatibleCloudProvider()

    assert asyncio.run(provider.health_check()) is False


def test_health_check_true_with_api_key(monkeypatch):
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "sk-test")
    provider = OpenAICompatibleCloudProvider()

    assert asyncio.run(provider.health_check()) is True


def test_complete_sends_bearer_auth_and_parses_response(monkeypatch):
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "sk-test")
    provider = OpenAICompatibleCloudProvider()

    captured = {}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {"message": {"content": "hi there"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2},
            }

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _Response()

    monkeypatch.setattr(
        "app.providers.cloud.httpx.AsyncClient", lambda *a, **k: _Client()
    )

    result = asyncio.run(
        provider.complete("gpt-4o-mini", [{"role": "user", "content": "hi"}])
    )

    assert result.text == "hi there"
    assert result.completion_tokens == 2
    assert result.prompt_tokens == 5
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["json"]["model"] == "gpt-4o-mini"
