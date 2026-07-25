from abc import ABC, abstractmethod

import psutil

from app.hardware.hardware_profile import HardwareProfile


class HardwareProvider(ABC):
    """
    Abstract base class for hardware detection.

    The Decision Engine only ever receives a HardwareProfile -- it
    never knows how that profile was collected.
    """

    @abstractmethod
    def detect(self) -> HardwareProfile:
        """
        Return the current hardware profile.
        """
        raise NotImplementedError


class LocalHardwareProvider(HardwareProvider):
    """
    Detects hardware for the machine LAIR is running on.

    Only system RAM is measured reliably today. GPU VRAM is always
    reported as unknown -- there is no NVIDIA GPU on this reference
    machine, and Windows' WMI AdapterRAM field is known to misreport
    for modern GPUs, so guessing would be worse than not knowing.
    """

    def detect(self) -> HardwareProfile:
        memory = psutil.virtual_memory()

        return HardwareProfile(
            total_ram_gb=memory.total / (1024**3),
            available_ram_gb=memory.available / (1024**3),
            gpu_vram_gb=None,
        )


hardware_provider = LocalHardwareProvider()
