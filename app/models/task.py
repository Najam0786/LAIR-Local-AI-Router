from pydantic import BaseModel, Field


class Task(BaseModel):
    """
    Domain representation of work to perform, independent of transport.

    HTTP, CLI, SDK and other adapters all translate their input
    into a Task before it reaches the Decision Engine.
    """

    prompt: str

    conversation_turns: int = Field(
        default=1,
        ge=1,
        description="Number of messages in the originating conversation, "
        "including this one. Feeds ComplexityTriage's conversation-depth "
        "signal (I-04); callers with no conversation notion (e.g. /route) "
        "leave this at the default.",
    )
