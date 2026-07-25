import socket
import sys

import httpx
import psutil
from pydantic import BaseModel

from app.core.settings import settings
from app.hardware.gpu_detector import (
    detect_apple_unified_memory,
    detect_nvidia_vram_gb,
)
from app.hardware.ssd_benchmark import benchmark_ssd_read_speed_gb_s, streaming_viability
from app.hardware.tier import HardwareTier, classify_tier

MINIMUM_PYTHON = (3, 13)


class DoctorReport(BaseModel):
    """
    Full machine profile + environment check, as printed by
    `python -m lair doctor` (I-02).
    """

    total_ram_gb: float
    available_ram_gb: float
    cpu_cores: int | None

    apple_unified_memory: bool
    gpu_vram_gb: float | None
    has_usable_gpu: bool

    tier: HardwareTier

    python_version: str
    python_ok: bool

    lm_studio_reachable: bool
    port_free: bool

    # I-16: real, best-effort sequential-read benchmark + a derived
    # 0.0-1.0 viability score for the SSD-streaming routing tier. See
    # ssd_benchmark.py for this measurement's honest limitations.
    ssd_read_speed_gb_s: float | None = None
    streaming_viability: float = 0.0

    problems: list[str]


async def run_doctor() -> DoctorReport:
    """
    Profiles this machine and checks the environment LAIR needs.

    Never raises -- every individual check degrades to "unknown"/False
    plus a problem entry rather than aborting the whole report, since a
    diagnostic tool that crashes on the first bad signal is worse than
    useless.
    """

    memory = psutil.virtual_memory()
    total_ram_gb = memory.total / (1024**3)
    available_ram_gb = memory.available / (1024**3)
    cpu_cores = psutil.cpu_count(logical=True)

    apple_unified_memory = detect_apple_unified_memory()
    gpu_vram_gb = None if apple_unified_memory else detect_nvidia_vram_gb()
    has_usable_gpu = apple_unified_memory or gpu_vram_gb is not None

    tier = classify_tier(total_ram_gb, has_usable_gpu)

    python_ok = sys.version_info[:2] >= MINIMUM_PYTHON
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    lm_studio_reachable = await _check_lm_studio_reachable()
    port_free = _check_port_free(settings.HOST, settings.PORT)

    ssd_read_speed_gb_s = benchmark_ssd_read_speed_gb_s()
    viability = streaming_viability(ssd_read_speed_gb_s)

    problems: list[str] = []

    if not python_ok:
        problems.append(
            f"Python {python_version} detected; LAIR targets "
            f"{MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+. "
            "Fix: install Python 3.13+ and recreate the virtualenv."
        )

    if not lm_studio_reachable:
        problems.append(
            f"LM Studio not reachable at {settings.LM_STUDIO_URL}. "
            "Fix: start LM Studio and enable its local server "
            "(Developer tab -> Start Server), or set LM_STUDIO_URL."
        )

    if not port_free:
        problems.append(
            f"Port {settings.PORT} on {settings.HOST} is already in use. "
            "Fix: stop whatever is using it, or set PORT in .env."
        )

    return DoctorReport(
        total_ram_gb=total_ram_gb,
        available_ram_gb=available_ram_gb,
        cpu_cores=cpu_cores,
        apple_unified_memory=apple_unified_memory,
        gpu_vram_gb=gpu_vram_gb,
        has_usable_gpu=has_usable_gpu,
        tier=tier,
        python_version=python_version,
        python_ok=python_ok,
        lm_studio_reachable=lm_studio_reachable,
        port_free=port_free,
        ssd_read_speed_gb_s=ssd_read_speed_gb_s,
        streaming_viability=viability,
        problems=problems,
    )


async def _check_lm_studio_reachable() -> bool:
    try:
        async with httpx.AsyncClient(
            timeout=settings.LMS_PROBE_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(f"{settings.LM_STUDIO_URL}/models")
            return response.status_code < 500
    except Exception:
        return False


def _check_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        # A successful connect means something is already listening
        # there; a failed one means the port is free to bind.
        return sock.connect_ex((host, port)) != 0
