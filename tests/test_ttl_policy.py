from app.execution.ttl_policy import (
    GENERALIST_TTL_SECONDS,
    SPECIALIST_TTL_SECONDS,
    TtlPolicy,
)
from tests.conftest import FAKE_MODELS


def test_small_model_gets_generalist_ttl():
    policy = TtlPolicy()

    # "qwen3-8b" -> ~8B params, under the generalist threshold.
    model = FAKE_MODELS[0]

    assert policy.ttl_seconds_for(model) == GENERALIST_TTL_SECONDS


def test_large_model_gets_specialist_ttl():
    policy = TtlPolicy()

    # "deepseek-r1-distill-qwen-32b" -> ~32B params, over the threshold.
    model = FAKE_MODELS[2]

    assert policy.ttl_seconds_for(model) == SPECIALIST_TTL_SECONDS


def test_unparseable_model_id_defaults_to_generalist_ttl():
    from app.capabilities.profile import CapabilityProfile
    from app.models.ai_model import AIModel

    policy = TtlPolicy()
    model = AIModel(
        id="custom-model-no-size",
        provider="test",
        profile=CapabilityProfile(
            model_id="custom-model-no-size", provider="test", capabilities=[]
        ),
    )

    assert policy.ttl_seconds_for(model) == GENERALIST_TTL_SECONDS
