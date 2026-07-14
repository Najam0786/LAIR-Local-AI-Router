from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.routing_engine import routing_engine


def _model(model_id: str, loaded: bool) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=loaded,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
        ),
    )


def test_loaded_model_preferred_when_scores_otherwise_equal():
    loaded = _model("loaded-model", loaded=True)
    not_loaded = _model("not-loaded-model", loaded=False)

    plan = routing_engine.route(
        Task(prompt="hello"),
        [not_loaded, loaded],
    )

    assert plan.decision.selected_model.id == "loaded-model"


def test_unloaded_model_is_selected_when_it_is_the_only_candidate():
    not_loaded = _model("not-loaded-model", loaded=False)

    plan = routing_engine.route(Task(prompt="hello"), [not_loaded])

    assert plan.decision.selected_model.id == "not-loaded-model"
