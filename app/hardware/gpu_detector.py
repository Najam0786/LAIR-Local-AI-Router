import platform
import re
import subprocess

_MEMORY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")


def detect_apple_unified_memory() -> bool:
    """
    Apple Silicon shares one memory pool between CPU and GPU -- system
    RAM effectively *is* usable "VRAM" there, unlike a discrete GPU.
    """

    return platform.system() == "Darwin" and platform.machine() == "arm64"


def detect_nvidia_vram_gb() -> float | None:
    """
    Best-effort NVIDIA VRAM detection via `nvidia-smi`, for the one-shot
    `lair doctor` report only.

    Deliberately not used on the live routing hot path -- see
    LocalHardwareProvider's docstring: on this project's reference
    machine, GPU memory reporting (WMI AdapterRAM, driver quirks) was
    unreliable enough that "unknown" was judged better than a
    confidently wrong number feeding routing decisions every request.
    A diagnostic report the user reads once can afford to try harder
    and simply say so when detection fails.
    """

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            timeout=5,
            text=True,
        )
    except Exception:
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    first_line = result.stdout.strip().splitlines()[0]
    match = _MEMORY_PATTERN.search(first_line)

    if not match:
        return None

    return float(match.group(1)) / 1024  # MiB -> GiB
