import json

from app.hardware.tier import HardwareTier
from app.registry.compact_models import (
    CompactModelCatalog,
    CompactModelCatalogLoader,
    CompactModelEntry,
)
from app.routing.provenance import Provenance


def test_loader_returns_empty_catalog_when_file_missing(tmp_path):
    loader = CompactModelCatalogLoader(path=tmp_path / "no-such-catalog.json")

    catalog = loader.load()

    assert catalog.all() == []


def test_loader_parses_a_real_catalog_file(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            [
                {
                    "model_id": "tiny-compact",
                    "source_model_id": "tiny",
                    "compression_method": "tensor-train-matrix (MPO)",
                    "size_reduction_pct": 90.0,
                    "quality_retention_pct": 92.0,
                    "tier_fit": "entry",
                }
            ]
        ),
        encoding="utf-8",
    )
    loader = CompactModelCatalogLoader(path=path)

    catalog = loader.load()
    entries = catalog.all()

    assert len(entries) == 1
    assert entries[0].provenance == Provenance.MEASURED
    assert entries[0].tier_fit == HardwareTier.ENTRY


def test_for_tier_filters_correctly():
    catalog = CompactModelCatalog(
        [
            CompactModelEntry(
                model_id="a",
                source_model_id="a-src",
                compression_method="tensor-train-matrix (MPO)",
                size_reduction_pct=90.0,
                quality_retention_pct=91.0,
                tier_fit=HardwareTier.ENTRY,
            ),
            CompactModelEntry(
                model_id="b",
                source_model_id="b-src",
                compression_method="tensor-train-matrix (MPO)",
                size_reduction_pct=85.0,
                quality_retention_pct=93.0,
                tier_fit=HardwareTier.ENTHUSIAST,
            ),
        ]
    )

    assert [e.model_id for e in catalog.for_tier(HardwareTier.ENTRY)] == ["a"]
