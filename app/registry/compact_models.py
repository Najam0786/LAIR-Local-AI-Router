import json
from pathlib import Path

from pydantic import BaseModel

from app.hardware.tier import HardwareTier
from app.routing.provenance import Provenance

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CATALOG_PATH = _ROOT / "configs" / "compact_models" / "catalog.json"


class CompactModelEntry(BaseModel):
    """
    One vetted, tensor-network-compressed model (I-19, RFC-0003).
    `provenance` is always MEASURED -- this catalog exists specifically
    to carry real before/after benchmark scores, never a guess.
    """

    model_id: str
    source_model_id: str
    compression_method: str
    size_reduction_pct: float
    quality_retention_pct: float
    tier_fit: HardwareTier
    provenance: Provenance = Provenance.MEASURED


class CompactModelCatalog:
    """Read-only view over a static, checked-in compact-model catalog."""

    def __init__(self, entries: list[CompactModelEntry]):
        self._entries = entries

    def all(self) -> list[CompactModelEntry]:
        return list(self._entries)

    def for_tier(self, tier: HardwareTier) -> list[CompactModelEntry]:
        return [entry for entry in self._entries if entry.tier_fit == tier]


class CompactModelCatalogLoader:
    def __init__(self, path: Path | str = _DEFAULT_CATALOG_PATH):
        self._path = Path(path)

    def load(self) -> CompactModelCatalog:
        if not self._path.exists():
            return CompactModelCatalog([])

        text = self._path.read_text(encoding="utf-8").strip()

        if not text:
            return CompactModelCatalog([])

        return CompactModelCatalog(
            [CompactModelEntry(**record) for record in json.loads(text)]
        )


compact_model_catalog_loader = CompactModelCatalogLoader()
