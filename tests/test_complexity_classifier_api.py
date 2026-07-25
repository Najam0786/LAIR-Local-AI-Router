import app.api.chat as chat_api_module
from app.core.settings import settings
from app.providers.completion_result import CompletionResult
from tests.conftest import FAKE_MODELS, FakeProvider


def test_model_assisted_classification_feeds_into_routing_decision(
    client, clean_registry, monkeypatch
):
    monkeypatch.setattr(settings, "ENABLE_MODEL_ASSISTED_COMPLEXITY", True)
    monkeypatch.setattr(settings, "COMPLEXITY_CLASSIFIER_MODEL_ID", "qwen3-8b")

    reasoning_model = FAKE_MODELS[2]  # deepseek-r1-distill-qwen-32b, REASONING
    classifier_and_target = FakeProvider(
        list(FAKE_MODELS),
        completions={
            "qwen3-8b": CompletionResult(
                text='{"complexity": 5, "task_type": "hard"}',
                completion_tokens=10,
                latency_seconds=0.1,
            )
        },
    )
    clean_registry.register(classifier_and_target)

    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 200

    records = chat_api_module.default_decision_repository.all()
    decision = records[-1]

    assert decision.complexity is not None
    assert decision.complexity.level == 5
    assert decision.selected_model.id == reasoning_model.id


def test_classifier_disabled_by_default_uses_rules_based_triage(
    client, registered_fake_provider
):
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 200

    records = chat_api_module.default_decision_repository.all()
    decision = records[-1]

    # "hi" is trivial under the rules-based triage -- level stays at 1.
    assert decision.complexity is not None
    assert decision.complexity.level == 1
