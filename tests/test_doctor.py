import asyncio
from unittest.mock import MagicMock

import app.hardware.doctor as doctor_module
from app.hardware.tier import HardwareTier


def _mock_memory(total_gb: float, available_gb: float) -> MagicMock:
    return MagicMock(
        total=total_gb * (1024**3),
        available=available_gb * (1024**3),
    )


def _run_doctor_with(
    monkeypatch,
    *,
    total_gb: float,
    available_gb: float,
    apple: bool,
    nvidia_vram_gb: float | None,
    lm_studio_reachable: bool,
    port_free: bool,
):
    monkeypatch.setattr(
        doctor_module.psutil,
        "virtual_memory",
        lambda: _mock_memory(total_gb, available_gb),
    )
    monkeypatch.setattr(doctor_module.psutil, "cpu_count", lambda logical=True: 8)
    monkeypatch.setattr(
        doctor_module, "detect_apple_unified_memory", lambda: apple
    )
    monkeypatch.setattr(
        doctor_module, "detect_nvidia_vram_gb", lambda: nvidia_vram_gb
    )

    async def _fake_lm_studio_reachable():
        return lm_studio_reachable

    monkeypatch.setattr(
        doctor_module, "_check_lm_studio_reachable", _fake_lm_studio_reachable
    )
    monkeypatch.setattr(
        doctor_module, "_check_port_free", lambda host, port: port_free
    )

    return asyncio.run(doctor_module.run_doctor())


def test_entry_tier_profile(monkeypatch):
    report = _run_doctor_with(
        monkeypatch,
        total_gb=6.0,
        available_gb=4.0,
        apple=False,
        nvidia_vram_gb=4.0,
        lm_studio_reachable=True,
        port_free=True,
    )

    assert report.tier == HardwareTier.ENTRY
    assert report.has_usable_gpu is True
    assert report.problems == []


def test_standard_tier_profile(monkeypatch):
    report = _run_doctor_with(
        monkeypatch,
        total_gb=16.0,
        available_gb=10.0,
        apple=False,
        nvidia_vram_gb=8.0,
        lm_studio_reachable=True,
        port_free=True,
    )

    assert report.tier == HardwareTier.STANDARD


def test_enthusiast_tier_profile_via_apple_unified_memory(monkeypatch):
    report = _run_doctor_with(
        monkeypatch,
        total_gb=64.0,
        available_gb=40.0,
        apple=True,
        nvidia_vram_gb=None,
        lm_studio_reachable=True,
        port_free=True,
    )

    assert report.tier == HardwareTier.ENTHUSIAST
    assert report.apple_unified_memory is True
    assert report.gpu_vram_gb is None


def test_cpu_only_tier_profile_regardless_of_ram(monkeypatch):
    report = _run_doctor_with(
        monkeypatch,
        total_gb=64.0,
        available_gb=40.0,
        apple=False,
        nvidia_vram_gb=None,
        lm_studio_reachable=True,
        port_free=True,
    )

    assert report.tier == HardwareTier.CPU_ONLY
    assert report.has_usable_gpu is False


def test_problems_reported_for_unreachable_lm_studio_and_busy_port(monkeypatch):
    report = _run_doctor_with(
        monkeypatch,
        total_gb=16.0,
        available_gb=10.0,
        apple=False,
        nvidia_vram_gb=8.0,
        lm_studio_reachable=False,
        port_free=False,
    )

    assert report.lm_studio_reachable is False
    assert report.port_free is False
    assert len(report.problems) == 2
    assert any("LM Studio" in problem for problem in report.problems)
    assert any("Port" in problem for problem in report.problems)
