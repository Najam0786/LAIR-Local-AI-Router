from pydantic import BaseModel


class ChatMessage(BaseModel):
    """
    One turn in an OpenAI-style chat request.
    """

    role: str
    content: str


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
