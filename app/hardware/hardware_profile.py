from pydantic import BaseModel


class HardwareProfile(BaseModel):
    """
    Describes the machine LAIR is running on.
    """

    total_ram_gb: float

    available_ram_gb: float

    gpu_vram_gb: float | None = None
