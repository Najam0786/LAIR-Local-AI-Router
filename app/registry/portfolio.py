from pathlib import Path

import yaml
from pydantic import BaseModel

from app.hardware.tier import HardwareTier

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PORTFOLIOS_DIR = _ROOT / "configs" / "portfolios"
_DEFAULT_ACTIVE_PORTFOLIO_PATH = _ROOT / "configs" / "active_portfolio.yaml"


class PortfolioModel(BaseModel):
    """
    One recommended model within a tier portfolio. Never auto-downloaded
    -- `lm_studio_search` is a search term for the user to enter in LM
    Studio's own model catalog (I-02 design constraint).
    """

    name: str
    lm_studio_search: str
    role: str
    notes: str = ""


class Portfolio(BaseModel):
    """
    A hardware tier's recommended model set, loaded from
    configs/portfolios/{tier}.yaml.
    """

    tier: HardwareTier
    description: str
    default_context_length: int
    # Recommended KV-cache precision for this tier (I-17) --
    # "fp16"/"int8"/"q4". A recommendation for the user to apply in LM
    # Studio's own load settings, not something LAIR sets remotely.
    kv_cache_recommendation: str = "fp16"
    # This machine's streaming_viability (I-16), attached by `lair
    # doctor --init` from its own real SSD benchmark -- None until a
    # doctor run has populated it; not part of the static per-tier
    # portfolio file itself (see configs/portfolios/*.yaml).
    streaming_viability: float | None = None
    models: list[PortfolioModel]


class PortfolioLoader:
    """
    Reads the static, checked-in tier portfolio definitions.
    """

    def __init__(self, directory: Path | str = _DEFAULT_PORTFOLIOS_DIR):
        self._directory = Path(directory)

    def load(self, tier: HardwareTier) -> Portfolio | None:
        path = self._directory / f"{tier.value}.yaml"

        if not path.exists():
            return None

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        return Portfolio(**data)


class PortfolioStore:
    """
    Persists the user's chosen tier portfolio as a single active
    recommendation record (`configs/active_portfolio.yaml`).

    This is not a second source of truth for which models exist --
    LAIR's live model list always comes from the provider (ADR-0002).
    It only records which tier/portfolio `lair doctor --init` last
    recommended, for tools that want to read it later (e.g. a future
    `lair install`).
    """

    def __init__(self, path: Path | str = _DEFAULT_ACTIVE_PORTFOLIO_PATH):
        self._path = Path(path)

    def save(self, portfolio: Portfolio) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            yaml.safe_dump(
                portfolio.model_dump(mode="json"),
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def load(self) -> Portfolio | None:
        if not self._path.exists():
            return None

        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}

        return Portfolio(**data)


portfolio_loader = PortfolioLoader()
default_portfolio_store = PortfolioStore()
