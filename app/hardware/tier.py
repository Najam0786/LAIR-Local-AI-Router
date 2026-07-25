from enum import Enum


class HardwareTier(str, Enum):
    """
    Hardware tiers LAIR recommends a model portfolio for (I-02).
    """

    ENTRY = "entry"
    STANDARD = "standard"
    ENTHUSIAST = "enthusiast"
    CPU_ONLY = "cpu_only"


ENTRY_MAX_RAM_GB = 8.0
STANDARD_MAX_RAM_GB = 16.0


def classify_tier(total_ram_gb: float, has_usable_gpu: bool) -> HardwareTier:
    """
    Assigns a hardware tier from total RAM and GPU availability.

    A machine with no usable GPU is always CPU_ONLY regardless of RAM --
    it needs CPU-friendly model choices a RAM-only tier wouldn't
    capture, per docs/INNOVATION_PLAN_2026.md I-02. `has_usable_gpu`
    should already account for Apple Silicon's unified memory counting
    as "usable GPU" for this purpose.
    """

    if not has_usable_gpu:
        return HardwareTier.CPU_ONLY

    if total_ram_gb <= ENTRY_MAX_RAM_GB:
        return HardwareTier.ENTRY

    if total_ram_gb <= STANDARD_MAX_RAM_GB:
        return HardwareTier.STANDARD

    return HardwareTier.ENTHUSIAST
