import pytest

from app.hardware.resource_resolver import (
    _BYTES_PER_GB,
    _KV_FP16_BYTES_PER_TOKEN_PER_BILLION_PARAMS,
    detect_moe,
    resource_resolver,
)
from app.providers.model_metadata import ModelMetadata


def _expected_kv_gb(params_billions: float, context_length: int) -> float:
    return (
        params_billions
        * context_length
        * _KV_FP16_BYTES_PER_TOKEN_PER_BILLION_PARAMS
        / _BYTES_PER_GB
    )


def test_parses_parameter_count_from_model_id():
    profile = resource_resolver.resolve("deepseek-r1-distill-qwen-32b")

    assert profile.estimated_ram_gb == 32 * 0.7


def test_parses_decimal_parameter_count():
    profile = resource_resolver.resolve("phi-3.5b-instruct")

    assert profile.estimated_ram_gb == 3.5 * 0.7


def test_unparseable_model_id_returns_unknown():
    profile = resource_resolver.resolve("text-embedding-nomic-embed-text-v1.5")

    assert profile.estimated_ram_gb is None


def test_known_quantization_changes_estimate():
    default_profile = resource_resolver.resolve("deepseek-r1-distill-qwen-32b")

    metadata = ModelMetadata(quantization="Q4_K_M")
    quantized_profile = resource_resolver.resolve(
        "deepseek-r1-distill-qwen-32b", metadata=metadata
    )

    assert quantized_profile.estimated_ram_gb == 32 * 0.55
    assert quantized_profile.estimated_ram_gb != default_profile.estimated_ram_gb


def test_unrecognized_quantization_falls_back_to_default():
    metadata = ModelMetadata(quantization="totally-unknown-format")

    profile = resource_resolver.resolve(
        "deepseek-r1-distill-qwen-32b", metadata=metadata
    )

    assert profile.estimated_ram_gb == 32 * 0.7


def test_no_context_window_skips_kv_estimation():
    profile = resource_resolver.resolve("deepseek-r1-distill-qwen-32b")

    assert profile.estimated_kv_cache_gb is None
    assert profile.estimated_total_ram_gb is None
    assert profile.effective_ram_gb == profile.estimated_ram_gb


def test_context_window_adds_kv_cache_and_total():
    profile = resource_resolver.resolve(
        "deepseek-r1-distill-qwen-32b", context_window=8192
    )

    expected_kv = _expected_kv_gb(32, 8192)

    assert profile.estimated_kv_cache_gb == expected_kv
    assert profile.estimated_total_ram_gb == profile.estimated_ram_gb + expected_kv
    assert profile.effective_ram_gb == profile.estimated_total_ram_gb


def test_larger_context_window_means_larger_kv_estimate():
    small_context = resource_resolver.resolve("qwen3-8b", context_window=4096)
    large_context = resource_resolver.resolve("qwen3-8b", context_window=32768)

    assert large_context.estimated_kv_cache_gb > small_context.estimated_kv_cache_gb


# (params_billions-implying model id, context_length, available_ram_gb,
# expected recommendation) -- covers a representative context-length
# scenario on each of I-02's four hardware tiers.
KV_RECOMMENDATION_SCENARIOS = [
    # ENTRY-like: small model, small context, plenty of headroom -> fp16 fine.
    ("qwen3.5-4b", 4096, 8.0, "fp16"),
    # CPU_ONLY-like: same shape, tighter budget -> needs int8.
    ("qwen3.5-4b", 4096, 3.5, "int8"),
    # STANDARD-like: 8B model, 8192 context, 16GB available -> fp16 fine.
    ("qwen3-8b", 8192, 16.0, "fp16"),
    # ENTHUSIAST-like: even a well-resourced 64GB machine still
    # benefits from a KV recommendation for a 32B model at full 32K
    # context -- fp16 alone needs ~95.5GB, int8 fits comfortably.
    ("deepseek-r1-distill-qwen-32b", 32768, 64.0, "int8"),
    # Constrained enough that even q4 KV can't make it fit.
    ("deepseek-r1-distill-qwen-32b", 65536, 4.0, None),
]


@pytest.mark.parametrize(
    "model_id,context_length,available_ram_gb,expected",
    KV_RECOMMENDATION_SCENARIOS,
)
def test_kv_cache_quant_recommendation_across_tiers(
    model_id, context_length, available_ram_gb, expected
):
    profile = resource_resolver.resolve(
        model_id,
        context_window=context_length,
        available_ram_gb=available_ram_gb,
    )

    assert profile.kv_cache_quant_recommended == expected


def test_recommend_kv_quant_prefers_least_lossy_that_fits():
    # 8B model, 32768 context: fp16 total (~23.9GB) is too big for
    # 15GB, but int8 (~14.7GB) fits alongside the weights.
    weights_gb = 8 * 0.7
    recommendation = resource_resolver.recommend_kv_quant(
        params_billions=8,
        context_window=32768,
        weights_gb=weights_gb,
        available_ram_gb=15.0,
    )

    assert recommendation == "int8"


def test_detect_moe_matches_active_param_suffix():
    is_moe, active_params_b = detect_moe("qwen3.6-35b-a3b")

    assert is_moe is True
    assert active_params_b == 3.0


def test_detect_moe_false_for_dense_model():
    is_moe, active_params_b = detect_moe("deepseek-r1-distill-qwen-32b")

    assert is_moe is False
    assert active_params_b is None


def test_detect_moe_does_not_confuse_base_param_count_for_active_suffix():
    # "qwen2.5-vl-7b" has a "7b" but no "-a<n>b" active-param suffix.
    is_moe, active_params_b = detect_moe("qwen2.5-vl-7b")

    assert is_moe is False
    assert active_params_b is None
