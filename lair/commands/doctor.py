from app.hardware.doctor import DoctorReport, run_doctor
from app.registry.portfolio import (
    Portfolio,
    PortfolioLoader,
    PortfolioStore,
    default_portfolio_store,
    portfolio_loader,
)


def format_report(report: DoctorReport, portfolio: Portfolio | None) -> str:
    """
    Renders a DoctorReport (+ its recommended portfolio, if any) as the
    plain-text report `python -m lair doctor` prints. Split out from
    `run()` so formatting is testable without capturing stdout.
    """

    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("LAIR Doctor")
    lines.append("=" * 60)
    lines.append(f"Total RAM:       {report.total_ram_gb:.1f} GB")
    lines.append(f"Available RAM:   {report.available_ram_gb:.1f} GB")
    lines.append(f"CPU cores:       {report.cpu_cores}")

    if report.apple_unified_memory:
        lines.append("GPU:             Apple Silicon (unified memory)")
    elif report.gpu_vram_gb is not None:
        lines.append(f"GPU VRAM:        {report.gpu_vram_gb:.1f} GB")
    else:
        lines.append("GPU:             none detected")

    lines.append(
        f"Python:          {report.python_version} "
        f"({'OK' if report.python_ok else 'below minimum'})"
    )
    lines.append(
        f"LM Studio:       "
        f"{'reachable' if report.lm_studio_reachable else 'NOT reachable'}"
    )
    lines.append(f"Port free:       {'yes' if report.port_free else 'no'}")
    lines.append("")
    lines.append(f"Assigned tier:   {report.tier.value.upper()}")
    lines.append("")

    if portfolio is not None:
        lines.append(f"Recommended portfolio -- {portfolio.description}")
        lines.append(
            f"Suggested default context length: "
            f"{portfolio.default_context_length}"
        )
        lines.append("")

        for model in portfolio.models:
            lines.append(f"  - {model.name} ({model.role})")
            lines.append(f'    LM Studio search: "{model.lm_studio_search}"')
            if model.notes:
                lines.append(f"    {model.notes}")

        lines.append("")
        lines.append(
            "LAIR does not download models automatically -- search for "
            "each term above in LM Studio's model catalog and download "
            "the ones you want."
        )
    else:
        lines.append(f"No portfolio file found for tier '{report.tier.value}'.")

    if report.problems:
        lines.append("")
        lines.append("Problems found:")
        for problem in report.problems:
            lines.append(f"  - {problem}")
    else:
        lines.append("")
        lines.append("No environment problems detected.")

    return "\n".join(lines)


async def run(
    init: bool = False,
    loader: PortfolioLoader = portfolio_loader,
    store: PortfolioStore = default_portfolio_store,
) -> DoctorReport:
    """
    Runs the full doctor check, prints the report, and (if `init`)
    saves the recommended portfolio as the active one -- LAIR's
    one-command registry initialization (I-02).
    """

    report = await run_doctor()
    portfolio = loader.load(report.tier)

    print(format_report(report, portfolio))

    if init and portfolio is not None:
        store.save(
            portfolio.model_copy(
                update={"streaming_viability": report.streaming_viability}
            )
        )
        print(f"\nSaved as configs/active_portfolio.yaml")

    return report
