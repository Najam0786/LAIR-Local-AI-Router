import pytest

from app.routing.complexity import MAX_COMPLEXITY, MIN_COMPLEXITY, ComplexityTriage

triage = ComplexityTriage()

# (prompt, conversation_turns, minimum expected complexity level)
#
# Lower-bound assertions rather than exact levels: the point is that
# each signal *raises* complexity relative to a trivial prompt, not
# that the heuristic weights are pinned to one specific scheme.
TRIVIAL_PROMPTS = [
    "hi",
    "hello",
    "thanks",
    "what's up",
    "good morning",
    "how are you",
    "ok",
    "sounds good",
    "nice",
    "got it",
]

MODERATE_LENGTH_PROMPTS = [
    " ".join(["word"] * 90),
    " ".join(["token"] * 100),
]

LONG_PROMPTS = [
    " ".join(["word"] * 250),
    " ".join(["token"] * 300),
]

CODE_BLOCK_PROMPTS = [
    "what does this do?\n```python\nprint('hi')\n```",
    "fix this:\n```js\nconsole.log(1)\n```",
]

HARD_KEYWORD_PROMPTS = [
    "prove that the square root of 2 is irrational",
    "walk me through this step by step",
    "please refactor entire the authentication module",
    "architect a system for real-time chat",
    "design a system for high-throughput logging",
    "give a comprehensive overview of transformers",
    "explain this in depth",
    "go thoroughly through the tradeoffs here",
]


@pytest.mark.parametrize("prompt", TRIVIAL_PROMPTS)
def test_trivial_prompts_stay_at_minimum_complexity(prompt):
    assessment = triage.assess(prompt)

    assert assessment.level == MIN_COMPLEXITY


@pytest.mark.parametrize("prompt", MODERATE_LENGTH_PROMPTS)
def test_moderately_long_prompts_raise_complexity(prompt):
    baseline = triage.assess("hi").level
    assessment = triage.assess(prompt)

    assert assessment.level > baseline


@pytest.mark.parametrize("prompt", LONG_PROMPTS)
def test_long_prompts_raise_complexity_more_than_moderate(prompt):
    moderate = triage.assess(" ".join(["word"] * 90)).level
    assessment = triage.assess(prompt)

    assert assessment.level > moderate


@pytest.mark.parametrize("prompt", CODE_BLOCK_PROMPTS)
def test_code_block_presence_raises_complexity(prompt):
    baseline = triage.assess("hi").level
    assessment = triage.assess(prompt)

    assert assessment.level > baseline
    assert any("code block" in reason.lower() for reason in assessment.reasons)


@pytest.mark.parametrize("prompt", HARD_KEYWORD_PROMPTS)
def test_hard_keywords_raise_complexity(prompt):
    baseline = triage.assess("hi").level
    assessment = triage.assess(prompt)

    assert assessment.level > baseline


def test_deep_conversation_raises_complexity():
    shallow = triage.assess("hi", conversation_turns=1)
    deep = triage.assess("hi", conversation_turns=10)

    assert deep.level > shallow.level


def test_level_never_exceeds_bounds():
    # Stack every signal at once -- length, code block, several
    # keywords, deep conversation -- and confirm the level still clamps.
    kitchen_sink = (
        "prove step by step and architect a comprehensive, in depth, "
        "end-to-end design ```python\nprint(1)\n``` " + " ".join(["word"] * 400)
    )

    assessment = triage.assess(kitchen_sink, conversation_turns=20)

    assert MIN_COMPLEXITY <= assessment.level <= MAX_COMPLEXITY
    assert assessment.level == MAX_COMPLEXITY


def test_assessment_always_has_at_least_one_reason():
    assessment = triage.assess("hi")

    assert len(assessment.reasons) >= 1
