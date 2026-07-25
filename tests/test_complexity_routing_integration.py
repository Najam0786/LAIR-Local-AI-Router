from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.core.settings import settings
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.routing_engine import routing_engine


def _model(model_id: str, capabilities: list[CapabilityType]) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=False,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=c) for c in capabilities],
        ),
    )


def test_decision_record_carries_the_complexity_assessment():
    reasoning_model = _model("reasoning-model", [CapabilityType.REASONING])

    plan = routing_engine.route(
        Task(prompt="prove step by step that this comprehensive design works"),
        [reasoning_model],
    )

    assert plan.decision.complexity is not None
    assert plan.decision.complexity.level >= 2


def test_hard_prompt_prefers_reasoning_model_over_equal_non_reasoning_model():
    reasoning_model = _model("reasoning-model", [CapabilityType.REASONING])
    plain_model = _model("plain-model", [])

    # Stacks three independent signals (hard keyword, code block,
    # moderate length) to clear the default complexity_reasoning_threshold
    # of 4 -- a single signal (see test_decision_record_carries_the_
    # complexity_assessment above) only reaches level 2.
    hard_prompt = (
        "prove step by step why this works\n```python\nprint(1)\n```\n"
        + " ".join(["context"] * 90)
    )

    plan = routing_engine.route(
        Task(prompt=hard_prompt),
        [plain_model, reasoning_model],
    )

    assert plan.decision.complexity.level >= 4
    assert plan.decision.selected_model.id == "reasoning-model"


def test_triage_disabled_by_config_leaves_complexity_none_and_selection_unaffected(
    monkeypatch,
):
    monkeypatch.setattr(settings, "ENABLE_COMPLEXITY_TRIAGE", False)

    reasoning_model = _model("reasoning-model", [CapabilityType.REASONING])
    plain_model = _model("plain-model", [])

    hard_prompt = (
        "prove step by step why this works\n```python\nprint(1)\n```\n"
        + " ".join(["context"] * 90)
    )

    plan = routing_engine.route(
        Task(prompt=hard_prompt),
        [plain_model, reasoning_model],
    )

    assert plan.decision.complexity is None
    for candidate in plan.decision.candidates:
        assert candidate.breakdown.complexity_score == 0.0
