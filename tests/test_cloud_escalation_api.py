import app.api.chat as chat_api_module
from app.core.settings import settings
from app.providers.base import BaseProvider
from app.providers.completion_result import CompletionResult
from app.routing.cloud_escalation import CloudEscalator


class _FakeCloudProvider(BaseProvider):
    is_cloud = True

    def __init__(self, error: bool = False):
        self._error = error

    async def list_models(self):
        return []

    async def health_check(self):
        return True

    async def complete(self, model_id, messages, max_tokens=64, ttl_seconds=None):
        if self._error:
            raise RuntimeError("simulated cloud failure")
        return CompletionResult(
            text="cloud answer", completion_tokens=5, latency_seconds=0.1
        )


HARD_PROMPT = (
    "prove step by step why this works\n```python\nprint(1)\n```\n"
    + " ".join(["context"] * 90)
)


def _enable(monkeypatch, budget=10.0):
    monkeypatch.setattr(settings, "ENABLE_CLOUD_ESCALATION", True)
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "CLOUD_MONTHLY_BUDGET_USD", budget)
    monkeypatch.setattr(settings, "CLOUD_ESCALATION_COMPLEXITY_THRESHOLD", 4)
    monkeypatch.setattr(settings, "CLOUD_ESCALATION_LOCAL_CONFIDENCE_THRESHOLD", 1.1)


def test_hard_prompt_escalates_to_cloud_when_enabled(
    client, registered_fake_provider, monkeypatch
):
    _enable(monkeypatch)
    monkeypatch.setattr(
        chat_api_module,
        "default_cloud_escalator",
        CloudEscalator(provider=_FakeCloudProvider()),
    )

    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": HARD_PROMPT}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["content"] == "cloud answer"
    assert body["lair_meta"]["routed_to_cloud"] is True
    assert body["lair_meta"]["cloud_escalation_reason"] is not None
    assert body["lair_meta"]["estimated_savings_usd"] is None


def test_disabled_by_default_never_escalates_even_on_hard_prompt(
    client, registered_fake_provider
):
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": HARD_PROMPT}]},
    )

    assert response.status_code == 200
    assert response.json()["lair_meta"]["routed_to_cloud"] is False


def test_easy_prompt_never_escalates_even_when_enabled(
    client, registered_fake_provider, monkeypatch
):
    _enable(monkeypatch)
    monkeypatch.setattr(
        chat_api_module,
        "default_cloud_escalator",
        CloudEscalator(provider=_FakeCloudProvider()),
    )

    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 200
    assert response.json()["lair_meta"]["routed_to_cloud"] is False


def test_budget_exhaustion_mid_month_blocks_further_escalation(
    client, registered_fake_provider, monkeypatch
):
    _enable(monkeypatch, budget=0.000001)
    monkeypatch.setattr(
        chat_api_module,
        "default_cloud_escalator",
        CloudEscalator(provider=_FakeCloudProvider()),
    )

    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": HARD_PROMPT}]},
    )

    assert response.status_code == 200
    # Budget too small for even one escalation -- falls back to local.
    assert response.json()["lair_meta"]["routed_to_cloud"] is False


def test_cloud_failure_falls_back_to_local_execution(
    client, registered_fake_provider, monkeypatch
):
    _enable(monkeypatch)
    monkeypatch.setattr(
        chat_api_module,
        "default_cloud_escalator",
        CloudEscalator(provider=_FakeCloudProvider(error=True)),
    )

    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": HARD_PROMPT}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["lair_meta"]["routed_to_cloud"] is False
    # Local FakeProvider's canned response, proving the fallback worked.
    assert body["choices"][0]["message"]["content"] == "ok"


def test_successful_escalation_records_real_spend(
    client, registered_fake_provider, monkeypatch
):
    _enable(monkeypatch)
    monkeypatch.setattr(
        chat_api_module,
        "default_cloud_escalator",
        CloudEscalator(provider=_FakeCloudProvider()),
    )

    before = chat_api_module.default_cloud_budget_ledger.spent_this_month()

    client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": HARD_PROMPT}]},
    )

    after = chat_api_module.default_cloud_budget_ledger.spent_this_month()

    assert after > before


def test_streaming_requests_never_escalate(
    client, registered_fake_provider, monkeypatch
):
    _enable(monkeypatch)
    monkeypatch.setattr(
        chat_api_module,
        "default_cloud_escalator",
        CloudEscalator(provider=_FakeCloudProvider()),
    )

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": HARD_PROMPT}],
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        response.read()

    # No exception, and the cloud path was never invoked for a
    # streaming request -- confirmed indirectly by budget staying at 0.
    assert chat_api_module.default_cloud_budget_ledger.spent_this_month() == 0.0
