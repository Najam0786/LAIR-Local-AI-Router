from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.routing_engine import routing_engine


def _model(
    model_id: str,
    loaded: bool,
    context_window: int | None = None,
) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=loaded,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
            context_window=context_window,
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


def test_loaded_model_wins_a_near_tie_not_just_an_exact_tie():
    # Sized so the unloaded model's raw score (context_window_weight *
    # 400000 = 4.0) beats the loaded model's raw score (0.0) but by less
    # than RoutingPolicy.loaded_bonus_weight (5.0) -- the sticky bonus
    # should still flip the outcome to the already-loaded model (I-05).
    loaded = _model("loaded-model", loaded=True, context_window=None)
    not_loaded = _model(
        "not-loaded-model", loaded=False, context_window=400_000
    )

    plan = routing_engine.route(
        Task(prompt="hello"),
        [not_loaded, loaded],
    )

    assert plan.decision.selected_model.id == "loaded-model"


def test_unloaded_model_still_wins_when_gap_exceeds_the_sticky_bonus():
    # A large enough advantage (context_window_weight * 1_000_000 = 10.0)
    # exceeds the loaded_bonus_weight (5.0) -- the sticky bonus must not
    # override a genuinely better unloaded candidate.
    loaded = _model("loaded-model", loaded=True, context_window=None)
    not_loaded = _model(
        "not-loaded-model", loaded=False, context_window=1_000_000
    )

    plan = routing_engine.route(
        Task(prompt="hello"),
        [not_loaded, loaded],
    )

    assert plan.decision.selected_model.id == "not-loaded-model"
