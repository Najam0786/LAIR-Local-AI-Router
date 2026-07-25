# Community Benchmark Score Snapshots (I-12)

`snapshot.json` is a static, checked-in list of anonymized, community-contributed benchmark data points, loaded by `app.registry.community_scores.CommunityScoreLoader`. It ships empty (`[]`) -- no fabricated scores -- until real community contributions are collected and reviewed.

## Format

```json
[
  {
    "model_id": "qwen3-8b",
    "hardware_tier": "standard",
    "tokens_per_second": 42.5,
    "sample_count": 3
  }
]
```

`hardware_tier` is one of `entry` / `standard` / `enthusiast` / `cpu_only` (`app.hardware.tier.HardwareTier`).

## Contributing

Run `python -m lair doctor` to see this machine's assigned tier, then use `app.registry.community_scores.export_contribution()` (or a future `lair` CLI wrapper) against your own `benchmarks/knowledge_base.json` to produce a shareable, anonymized export -- model id, hardware tier, and measured tokens/sec only, never a prompt or anything else that could identify you or your usage. Open a PR adding your entries to `snapshot.json`.

## How it's used

`ModelScorer` only ever falls back to a community score when this machine has **no local measurement** for that model -- a local `MEASURED` result always overrides a `COMMUNITY` one, never the reverse.
