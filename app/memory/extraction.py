import re

# Case-insensitive patterns marking a message as containing a durable
# fact/preference/decision worth remembering (I-18, RFC-0002). A small,
# deliberately cheap rules phase -- mirroring I-04's own rules-first,
# model-assisted-later precedent -- rather than an inference call on
# every single exchange.
_TRIGGER_PATTERNS = [
    re.compile(r"\bremember\b", re.IGNORECASE),
    re.compile(r"\bmy name is\b", re.IGNORECASE),
    re.compile(r"\bi prefer\b", re.IGNORECASE),
    re.compile(r"\bi'?m using\b", re.IGNORECASE),
    re.compile(r"\bi am using\b", re.IGNORECASE),
    re.compile(r"\balways\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    re.compile(r"\bnote that\b", re.IGNORECASE),
    re.compile(r"\bimportant:", re.IGNORECASE),
]


def extract_candidate_memory(message: str) -> str | None:
    """
    Returns `message` verbatim if it matches a durable-statement
    pattern, `None` otherwise. Most messages should return `None` --
    that's correct, not a gap: not every exchange contains a fact worth
    remembering.
    """

    if not message or not message.strip():
        return None

    for pattern in _TRIGGER_PATTERNS:
        if pattern.search(message):
            return message.strip()

    return None
