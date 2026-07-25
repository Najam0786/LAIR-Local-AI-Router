import asyncio

from lair.commands import doctor as doctor_command
from app.hardware.doctor import DoctorReport
from app.hardware.tier import HardwareTier
from app.registry.portfolio import Portfolio, PortfolioLoader, PortfolioStore


def _fake_report(
    tier: HardwareTier = HardwareTier.STANDARD, streaming_viability: float = 0.0
) -> DoctorReport:
    return DoctorReport(
        total_ram_gb=16.0,
        available_ram_gb=10.0,
        cpu_cores=8,
        apple_unified_memory=False,
        gpu_vram_gb=8.0,
        has_usable_gpu=True,
        tier=tier,
        python_version="3.13.5",
        python_ok=True,
        lm_studio_reachable=True,
        port_free=True,
        ssd_read_speed_gb_s=None,
        streaming_viability=streaming_viability,
        problems=[],
    )


def test_format_report_includes_tier_and_models():
    report = _fake_report()
    portfolio = PortfolioLoader().load(report.tier)

    text = doctor_command.format_report(report, portfolio)

    assert "STANDARD" in text
    assert portfolio.models[0].name in text
    assert "LM Studio search:" in text


def test_format_report_handles_missing_portfolio():
    report = _fake_report()

    text = doctor_command.format_report(report, None)

    assert "No portfolio file found" in text


def test_run_saves_active_portfolio_when_init_true(monkeypatch, tmp_path):
    async def _fake_run_doctor():
        return _fake_report(HardwareTier.CPU_ONLY)

    monkeypatch.setattr(doctor_command, "run_doctor", _fake_run_doctor)

    store = PortfolioStore(path=tmp_path / "active_portfolio.yaml")
    loader = PortfolioLoader()

    assert store.load() is None

    asyncio.run(doctor_command.run(init=True, loader=loader, store=store))

    saved = store.load()
    assert saved is not None
    assert saved.tier == HardwareTier.CPU_ONLY


def test_run_saves_streaming_viability_from_the_doctor_report(monkeypatch, tmp_path):
    async def _fake_run_doctor():
        return _fake_report(HardwareTier.STANDARD, streaming_viability=0.65)

    monkeypatch.setattr(doctor_command, "run_doctor", _fake_run_doctor)

    store = PortfolioStore(path=tmp_path / "active_portfolio.yaml")
    loader = PortfolioLoader()

    asyncio.run(doctor_command.run(init=True, loader=loader, store=store))

    saved = store.load()
    assert saved.streaming_viability == 0.65


def test_run_does_not_save_when_init_false(monkeypatch, tmp_path):
    async def _fake_run_doctor():
        return _fake_report(HardwareTier.ENTRY)

    monkeypatch.setattr(doctor_command, "run_doctor", _fake_run_doctor)

    store = PortfolioStore(path=tmp_path / "active_portfolio.yaml")
    loader = PortfolioLoader()

    asyncio.run(doctor_command.run(init=False, loader=loader, store=store))

    assert store.load() is None
