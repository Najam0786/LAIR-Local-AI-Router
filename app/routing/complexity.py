import re

from pydantic import BaseModel, Field

MIN_COMPLEXITY = 1
MAX_COMPLEXITY = 5

_CODE_BLOCK_PATTERN = re.compile(r"```")

_LONG_PROMPT_WORDS = 200
_MODERATE_PROMPT_WORDS = 80
_DEEP_CONVERSATION_TURNS = 5

# Signals of a genuinely hard task, not just a long one. Deliberately
# small and literal (Phase 1 rules, per I-04) -- a model-assisted
# classifier is the planned Phase 2, not built here.
_HARD_KEYWORDS = (
    "prove",
    "step by step",
    "step-by-step",
    "refactor entire",
    "architect",
    "design a system",
    "comprehensive",
    "in depth",
    "in-depth",
    "thoroughly",
    "multi-step",
    "trade-off",
    "tradeoff",
    "end to end",
    "end-to-end",
)


class ComplexityAssessment(BaseModel):
    """
    Rules-based estimate of how difficult a request is to answer well,
    on a 1 (trivial) - 5 (hard) scale (I-04, Phase 1: rules only).
    """

    level: int = Field(ge=MIN_COMPLEXITY, le=MAX_COMPLEXITY)

    reasons: list[str] = Field(default_factory=list)


class ComplexityTriage:
    """
    Zero-cost complexity heuristics: prompt length, code-block presence,
    hard-task keywords, and conversation depth.

    Sits between capability extraction and candidate discovery in the
    routing pipeline (RoutingEngine.route()) -- it never touches models
    or hardware, only the request itself.
    """

    def assess(
        self,
        prompt: str,
        conversation_turns: int = 1,
    ) -> ComplexityAssessment:
        level = MIN_COMPLEXITY
        reasons: list[str] = []

        word_count = len(prompt.split())

        if word_count > _LONG_PROMPT_WORDS:
            level += 2
            reasons.append(f"Long prompt ({word_count} words)")
        elif word_count > _MODERATE_PROMPT_WORDS:
            level += 1
            reasons.append(f"Moderately long prompt ({word_count} words)")

        if _CODE_BLOCK_PATTERN.search(prompt):
            level += 1
            reasons.append("Contains a code block")

        lowered = prompt.lower()
        matched_keywords = [
            keyword for keyword in _HARD_KEYWORDS if keyword in lowered
        ]

        if matched_keywords:
            level += 1
            reasons.append(f"Hard-task keyword(s): {', '.join(matched_keywords)}")

        if conversation_turns > _DEEP_CONVERSATION_TURNS:
            level += 1
            reasons.append(f"Deep conversation ({conversation_turns} turns)")

        level = max(MIN_COMPLEXITY, min(MAX_COMPLEXITY, level))

        if not reasons:
            reasons.append("No complexity signals detected")

        return ComplexityAssessment(level=level, reasons=reasons)


complexity_triage = ComplexityTriage()
