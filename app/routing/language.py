from langdetect import DetectorFactory, LangDetectException, detect

# langdetect's Naive Bayes detector is otherwise non-deterministic
# (randomized tie-breaking) -- pin it once at import time so the same
# prompt always detects the same language, in production and in tests.
DetectorFactory.seed = 0

# Below this length, langdetect's confidence on short/ambiguous text is
# unreliable enough to misfire wildly (e.g. "hi" -> Swahili, "ok" ->
# Slovak, observed directly against this exact library). Treating a
# too-short prompt as "unknown" is graceful degradation (ADR-0011): a
# wrong guess actively steering routing is worse than no signal.
MIN_PROMPT_LENGTH_FOR_DETECTION = 15


def detect_language(prompt: str) -> str | None:
    """
    Best-effort ISO 639-1-ish language code for a prompt, or None when
    the prompt is too short or otherwise undetectable. Never raises.
    """

    if len(prompt.strip()) < MIN_PROMPT_LENGTH_FOR_DETECTION:
        return None

    try:
        return detect(prompt)
    except LangDetectException:
        return None
