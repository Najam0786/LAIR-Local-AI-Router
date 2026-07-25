# Compact Model Catalog (I-19)

`catalog.json` is a static, checked-in list of vetted, tensor-network-compressed models, loaded by `app.registry.compact_models.CompactModelCatalogLoader`. It ships empty (`[]`) -- no fabricated entries -- until a real model has actually been compressed, healed, and benchmarked (Phase 1b/2 of I-19; see `docs/rfcs/RFC-0003-lair-compact-models.md`).

## Format

```json
[
  {
    "model_id": "smollm3-3b-compactifai-q4",
    "source_model_id": "smollm3-3b",
    "compression_method": "tensor-train-matrix (MPO)",
    "size_reduction_pct": 92.5,
    "quality_retention_pct": 91.0,
    "tier_fit": "cpu_only",
    "provenance": "measured"
  }
]
```

`provenance` is always `"measured"` -- this catalog exists specifically to carry real before/after benchmark scores (per RFC-0003's quality bar: retained score >= 90% of the source model's own benchmark), never a guess.

## Current status

Empty. `scripts/compactify/pipeline.py` validates the tensor-train/MPO compression math on synthetic weight-shaped matrices (Phase 1a); compressing and benchmarking a real small open model (Phase 1b) is named future work, not yet done.
