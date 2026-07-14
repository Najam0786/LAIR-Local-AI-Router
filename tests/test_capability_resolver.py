from app.capabilities.capability import CapabilityType
from app.capabilities.resolver import resolver
from app.providers.model_metadata import ModelMetadata


def _capability_types(model_id: str) -> set[CapabilityType]:
    profile = resolver.resolve(model_id, "lmstudio")
    return {capability.type for capability in profile.capabilities}


def test_resolves_coding_capability():
    assert CapabilityType.CODING in _capability_types("qwen2.5-coder-32b")


def test_resolves_reasoning_capability_for_deepseek():
    assert CapabilityType.REASONING in _capability_types("deepseek-r1-distill-qwen-32b")


def test_resolves_vision_capability():
    assert CapabilityType.VISION in _capability_types("qwen2.5-vl-7b")


def test_resolves_embedding_capability():
    assert CapabilityType.EMBEDDING in _capability_types("text-embedding-nomic")


def test_plain_model_only_has_text_generation():
    assert _capability_types("gemma-4-26b") == {CapabilityType.TEXT_GENERATION}


def test_metadata_grounds_vision_regardless_of_model_id():
    metadata = ModelMetadata(is_vision=True)

    profile = resolver.resolve("some-unrelated-name", "lmstudio", metadata=metadata)

    assert CapabilityType.VISION in {c.type for c in profile.capabilities}


def test_metadata_grounds_tool_use():
    metadata = ModelMetadata(supports_tool_use=True)

    profile = resolver.resolve("some-model", "lmstudio", metadata=metadata)

    assert CapabilityType.TOOL_USE in {c.type for c in profile.capabilities}


def test_metadata_sets_context_window():
    metadata = ModelMetadata(context_window=131072)

    profile = resolver.resolve("some-model", "lmstudio", metadata=metadata)

    assert profile.context_window == 131072


def test_no_metadata_context_window_stays_none():
    profile = resolver.resolve("some-model", "lmstudio")

    assert profile.context_window is None


def test_reasoning_and_coding_stay_heuristic_even_with_metadata():
    metadata = ModelMetadata(is_vision=False)

    profile = resolver.resolve(
        "deepseek-r1-distill-qwen-32b", "lmstudio", metadata=metadata
    )

    assert CapabilityType.REASONING in {c.type for c in profile.capabilities}
