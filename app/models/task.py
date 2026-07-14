from pydantic import BaseModel


class Task(BaseModel):
    """
    Domain representation of work to perform, independent of transport.

    HTTP, CLI, SDK and other adapters all translate their input
    into a Task before it reaches the Decision Engine.
    """

    prompt: str
