from pydantic import BaseModel


class ResourceProfile(BaseModel):
    """
    Estimated resource requirement for running a model.

    Deliberately minimal: only RAM is estimable at all today.
    """

    estimated_ram_gb: float | None = None
