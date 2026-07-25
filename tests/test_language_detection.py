import pytest

from app.routing.language import MIN_PROMPT_LENGTH_FOR_DETECTION, detect_language

# (prompt, expected langdetect code) -- covers well over the 5 languages
# required by I-10's acceptance criteria.
LANGUAGE_CASES = [
    (
        "Hello, how are you doing today? I wanted to ask about the weather.",
        "en",
    ),
    (
        "Bonjour, comment allez-vous aujourd'hui? J'aimerais vous poser une question.",
        "fr",
    ),
    (
        "Hola, como estas hoy? Me gustaria hacerte una pregunta sobre el clima.",
        "es",
    ),
    (
        "Guten Tag, wie geht es dir heute? Ich wollte dich etwas fragen.",
        "de",
    ),
    (
        "你好,你今天过得怎么样?我想问你一个关于天气的问题。",
        "zh-cn",
    ),
    (
        "مرحبا كيف حالك اليوم؟ أردت أن أسألك سؤالا عن الطقس اليوم",
        "ar",
    ),
    (
        "नमस्ते आप आज कैसे हैं? मैं आपसे मौसम के बारे में एक सवाल पूछना चाहता था",
        "hi",
    ),
]


@pytest.mark.parametrize("prompt,expected", LANGUAGE_CASES)
def test_detect_language(prompt, expected):
    assert detect_language(prompt) == expected


def test_short_prompt_returns_none_rather_than_guessing():
    assert len("hi") < MIN_PROMPT_LENGTH_FOR_DETECTION
    assert detect_language("hi") is None
    assert detect_language("ok") is None


def test_empty_prompt_returns_none():
    assert detect_language("") is None
