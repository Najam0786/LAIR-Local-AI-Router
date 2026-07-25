import pytest

from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.policy import RoutingPolicy
from app.routing.selector import selector

TASK = Task(prompt="test prompt")


def _model(
    model_id: str,
    capabilities: list[Capability],
    context_window: int | None = None,
) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=capabilities,
            context_window=context_window,
        ),
    )


def test_select_raises_on_empty_models():
    with pytest.raises(ValueError):
        selector.select(TASK, [], [], RoutingPolicy())


def test_single_candidate_has_full_confidence():
    model = _model("a", [Capability(type=CapabilityType.CODING)])

    decision = selector.select(TASK, [model], [], RoutingPolicy())

    assert decision.selected_model.id == "a"
    assert decision.confidence == 1.0


def test_confidence_reflects_score_gap():
    strong = _model(
        "strong",
        [Capability(type=CapabilityType.CODING), Capability(type=CapabilityType.REASONING)],
        context_window=100000,
    )
    weak = _model("weak", [])
    requirements = [
        CapabilityRequirement(capability=CapabilityType.CODING),
        CapabilityRequirement(capability=CapabilityType.REASONING),
    ]

    decision = selector.select(TASK, [weak, strong], requirements, RoutingPolicy())

    assert decision.selected_model.id == "strong"
    assert 0.0 < decision.confidence <= 1.0


def test_near_tie_has_zero_confidence():
    a = _model("a", [Capability(type=CapabilityType.CODING)])
    b = _model("b", [Capability(type=CapabilityType.CODING)])
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING)]

    decision = selector.select(TASK, [a, b], requirements, RoutingPolicy())

    assert decision.confidence == 0.0


def test_reasons_reflect_winning_candidate():
    model = _model("a", [Capability(type=CapabilityType.CODING)])
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING)]

    decision = selector.select(TASK, [model], requirements, RoutingPolicy())

    assert any("coding" in reason for reason in decision.reasons)


def test_decision_record_retains_task_and_requirements():
    model = _model("a", [Capability(type=CapabilityType.CODING)])
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING)]

    decision = selector.select(TASK, [model], requirements, RoutingPolicy())

    assert decision.task == TASK
    assert decision.requirements == requirements
