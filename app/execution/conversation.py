from pydantic import BaseModel, field_validator


class ChatMessage(BaseModel):
    """
    One turn in an OpenAI-style chat request.
    """

    role: str
    content: str

    @field_validator("content", mode="before")
    @classmethod
    def _normalize_content(cls, value: object) -> object:
        """
        Some clients (e.g. Cline) send content as a list of parts
        (`[{"type": "text", "text": "..."}]`) instead of a plain string --
        both are valid per the OpenAI API. Non-text parts (e.g. images)
        are dropped: providers don't accept multimodal input yet.
        """

        if isinstance(value, list):
            return "".join(
                part.get("text", "")
                for part in value
                if isinstance(part, dict) and part.get("type") == "text"
            )

        return value


class Conversation(BaseModel):
    """
    Request-scoped transport payload -- the full message history sent
    by an OpenAI-compatible client on a single request.

    Not persisted, no session id: every client this is built for
    (Continue, Cline, Cursor, Open WebUI) already resends the complete
    history on every call, so there is nothing for LAIR to remember
    between requests.
    """

    messages: list[ChatMessage]

    def latest_user_message(self) -> str:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content

        raise ValueError("Conversation has no user message.")
