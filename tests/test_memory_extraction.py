import pytest

from app.memory.extraction import extract_candidate_memory


@pytest.mark.parametrize(
    "message",
    [
        "Please remember that I use tabs, not spaces.",
        "My name is Priya and I lead the backend team.",
        "I prefer concise answers with no filler.",
        "I'm using Python 3.13 for this project.",
        "I am using PostgreSQL for the database.",
        "Always run the linter before committing.",
        "Never touch the production database directly.",
        "Note that the API key rotates monthly.",
        "Important: the staging server is on a different port.",
    ],
)
def test_durable_statements_are_extracted_verbatim(message):
    assert extract_candidate_memory(message) == message


@pytest.mark.parametrize(
    "message",
    [
        "hi",
        "what does this function do?",
        "can you fix the bug in routing_engine.py?",
        "thanks, that worked",
    ],
)
def test_ordinary_messages_yield_no_candidate(message):
    assert extract_candidate_memory(message) is None


def test_empty_message_yields_no_candidate():
    assert extract_candidate_memory("") is None
    assert extract_candidate_memory("   ") is None
