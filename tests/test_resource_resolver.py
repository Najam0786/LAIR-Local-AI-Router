from app.hardware.resource_resolver import resource_resolver
from app.providers.model_metadata import ModelMetadata


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
