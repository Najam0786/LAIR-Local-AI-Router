from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.hardware_provider import HardwareProvider
from app.models.ai_model import AIModel
from app.models.task import Task
from app.providers.model_metadata import ModelMetadata
from app.routing.routing_engine import routing_engine


class _FixedHardwareProvider(HardwareProvider):
    def __init__(self, profile: HardwareProfile):
        self._profile = profile

    def detect(self) -> HardwareProfile:
        return self._profile


def _quant_variant(model_id: str, quantization: str) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=False,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
        ),
        metadata=ModelMetadata(quantization=quantization),
    )


def test_router_degrades_to_a_smaller_quant_under_memory_pressure_instead_of_oom():
    # Same 32B base model, two quant variants a user has downloaded.
    # Q4_K_M: 32 * 0.55 = 17.6GB. Q8_0: 32 * 1.1 = 35.2GB.
    q4_variant = _quant_variant("model-32b-q4", "Q4_K_M")
    q8_variant = _quant_variant("model-32b-q8", "Q8_0")

    # Only 20GB free -- the Q8 variant cannot possibly fit, the Q4
    # variant comfortably does.
    hardware_provider = _FixedHardwareProvider(
        HardwareProfile(total_ram_gb=32.0, available_ram_gb=20.0)
    )

    plan = routing_engine.route(
        Task(prompt="hello"),
        [q8_variant, q4_variant],
        hardware_provider=hardware_provider,
    )

    # Degradation, not failure: the smaller quant is chosen rather than
    # the request failing outright (ADR-0011 graceful degradation).
    assert plan.decision.selected_model.id == "model-32b-q4"

    candidate_ids = {c.model.id for c in plan.decision.candidates}
    assert candidate_ids == {"model-32b-q4"}


def test_router_prefers_larger_model_at_q4_over_smaller_model_at_q8_within_budget():
    # A bigger model at an efficient quant against a smaller model at
    # an inefficient one, both otherwise identical and both fitting --
    # I-03's "prefer larger-model-Q4 over smaller-model-Q8" preference.
    big_q4 = _quant_variant("big-model-q4", "Q4_K_M")
    small_q8 = _quant_variant("small-model-q8", "Q8_0")

    hardware_provider = _FixedHardwareProvider(
        HardwareProfile(total_ram_gb=64.0, available_ram_gb=64.0)
    )

    plan = routing_engine.route(
        Task(prompt="hello"),
        [small_q8, big_q4],
        hardware_provider=hardware_provider,
    )

    assert plan.decision.selected_model.id == "big-model-q4"


def test_decision_explanation_names_the_chosen_quant_and_why():
    q4_variant = _quant_variant("model-32b-q4", "Q4_K_M")

    hardware_provider = _FixedHardwareProvider(
        HardwareProfile(total_ram_gb=32.0, available_ram_gb=20.0)
    )

    plan = routing_engine.route(
        Task(prompt="hello"),
        [q4_variant],
        hardware_provider=hardware_provider,
    )

    assert any("Q4_K_M selected" in reason for reason in plan.decision.reasons)
