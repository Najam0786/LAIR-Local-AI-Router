from app.capabilities.capability import CapabilityType
from app.routing.request_analyzer import analyzer


def _capabilities(prompt: str) -> set[CapabilityType]:
    return {requirement.capability for requirement in analyzer.analyze(prompt)}


def test_always_requires_text_generation():
    assert CapabilityType.TEXT_GENERATION in _capabilities("hello there")


def test_detects_coding_keywords():
    assert CapabilityType.CODING in _capabilities("please debug this python function")


def test_detects_vision_keywords():
    assert CapabilityType.VISION in _capabilities("describe this image")


def test_detects_reasoning_keywords():
    assert CapabilityType.REASONING in _capabilities("reason through this logic puzzle")


def test_detects_translation_keyword():
    assert CapabilityType.TRANSLATION in _capabilities("translate this sentence")


def test_detects_summarization_keyword():
    assert CapabilityType.SUMMARIZATION in _capabilities("summarize this document")


def test_plain_prompt_only_requires_text_generation():
    assert _capabilities("what is the capital of france") == {
        CapabilityType.TEXT_GENERATION
    }
