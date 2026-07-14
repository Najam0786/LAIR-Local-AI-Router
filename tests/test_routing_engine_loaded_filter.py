from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.routing_engine import routing_engine
from app.routing.selector import NoCandidateModelsError

import pytest


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


def test_not_loaded_model_is_excluded_from_candidates():
    loaded = _model("loaded-model", loaded=True)
    not_loaded = _model("not-loaded-model", loaded=False)

    plan = routing_engine.route(
        Task(prompt="hello"),
        [not_loaded, loaded],
    )

    assert plan.decision.selected_model.id == "loaded-model"


def test_no_candidates_when_only_unloaded_models_exist():
    not_loaded = _model("not-loaded-model", loaded=False)

    with pytest.raises(NoCandidateModelsError):
        routing_engine.route(Task(prompt="hello"), [not_loaded])
