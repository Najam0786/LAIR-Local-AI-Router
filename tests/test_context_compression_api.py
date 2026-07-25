from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.models.ai_model import AIModel


def _small_context_model() -> AIModel:
    return AIModel(
        id="small-context-model",
        provider="fake",
        loaded=True,
        profile=CapabilityProfile(
            model_id="small-context-model",
            provider="fake",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
            context_window=4096,
        ),
    )


def test_fifty_turn_conversation_stays_functional_on_a_4k_context_model(
    client, clean_registry
):
    from tests.conftest import FakeProvider

    captured: dict = {}

    class _CapturingProvider(FakeProvider):
        async def complete(self, model_id, messages, *args, **kwargs):
            captured["messages"] = messages
            return await super().complete(model_id, messages, *args, **kwargs)

    model = _small_context_model()
    clean_registry.register(_CapturingProvider([model]))

    # 50 turns, each large enough that the full conversation would
    # otherwise blow well past a 4096-token window.
    messages = [
        {
            "role": "assistant" if i % 2 == 0 else "user",
            "content": " ".join(["word"] * 60) + f" turn {i}",
        }
        for i in range(50)
    ]

    response = client.post(
        "/v1/chat/completions",
        json={"messages": messages},
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "ok"

    # Real signal that compression actually ran, not just "didn't
    # crash" -- the provider received far fewer messages than were sent.
    assert len(captured["messages"]) < 50
    assert any("omitted" in m["content"] for m in captured["messages"])
