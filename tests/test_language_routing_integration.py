from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.core.settings import settings
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.routing_engine import routing_engine

SPANISH_PROMPT = (
    "Hola, como estas hoy? Me gustaria hacerte una pregunta sobre el clima "
    "y sobre como funciona este programa."
)


def _model(model_id: str) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=False,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
        ),
    )


def test_spanish_prompt_prefers_the_model_declared_strong_in_spanish():
    # "qwen" is declared multilingual (including Spanish) in
    # configs/language_strengths.yaml; "smollm" is declared English-only.
    multilingual = _model("qwen3-8b")
    english_only = _model("smollm3-3b")

    plan = routing_engine.route(
        Task(prompt=SPANISH_PROMPT),
        [english_only, multilingual],
    )

    assert plan.decision.language_code == "es"
    assert plan.decision.selected_model.id == "qwen3-8b"


def test_decision_explanation_names_the_detected_language():
    multilingual = _model("qwen3-8b")

    plan = routing_engine.route(
        Task(prompt=SPANISH_PROMPT),
        [multilingual],
    )

    assert any("'es'" in reason for reason in plan.decision.reasons)


def test_language_routing_disabled_by_config_leaves_language_code_none(
    monkeypatch,
):
    monkeypatch.setattr(settings, "ENABLE_LANGUAGE_ROUTING", False)

    multilingual = _model("qwen3-8b")
    english_only = _model("smollm3-3b")

    plan = routing_engine.route(
        Task(prompt=SPANISH_PROMPT),
        [english_only, multilingual],
    )

    assert plan.decision.language_code is None
    for candidate in plan.decision.candidates:
        assert candidate.breakdown.language_score == 0.0


def test_short_english_prompt_is_unaffected_by_language_routing():
    multilingual = _model("qwen3-8b")
    english_only = _model("smollm3-3b")

    plan = routing_engine.route(
        Task(prompt="hello"),
        [english_only, multilingual],
    )

    assert plan.decision.language_code is None
