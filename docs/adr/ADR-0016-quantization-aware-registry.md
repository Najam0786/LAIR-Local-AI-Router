# ADR-0016 — Quantization-Aware Registry

**Status:** Accepted

**Date:** 2026-07-25

---

# Context

`docs/INNOVATION_PLAN_2026.md` I-03 (Wave 2) asks LAIR to treat each quantization of a model as a distinct registry entry with its own memory footprint, and to prefer memory-efficient quants within budget (e.g. a bigger model at Q4 over a smaller one at Q8) rather than only ever hard-filtering on fit.

Two things were already true before this ADR and didn't need to be rebuilt:

- **Multiple quant entries per base model already work structurally.** LAIR's registry has no static per-model config file — models come live from `provider.list_models()` (ADR-0002). If a user has downloaded both a Q4 and a Q8 build of the same base model into LM Studio, both already appear as separate `AIModel` entries, each with its own `ModelMetadata.quantization` (ADR-0013).
- **Quantization already changes the memory estimate.** `ResourceResolver` has used a quantization-aware GB-per-billion-parameters table since ADR-0013, and `filter_by_hardware()` (ADR-0012) already hard-rejects a candidate whose estimate exceeds available RAM (plus reclaimable RAM from eviction). A too-big quant is already never OOM'd into — it's already filtered out.

What was actually missing, scoped to this pass:

1. No signal in scoring or explanations ever named *which quant* was chosen or *why* — a user watching two fitting candidates get ranked had no way to see the quantization reasoning.
2. No preference existed between two fitting quants of comparable capability — filtering only enforces "fits or doesn't," so a smaller-but-lower-quality Q8 build and a larger-but-more-efficient Q4 build ranked as ties on every other factor.
3. MoE-ness (LAIR's own portfolio already includes `-A3B`/`-A4B` models) wasn't surfaced anywhere, even informationally.

I-03's own design notes also call for KV-cache-aware memory estimation ("weights + KV cache, scales with context"). `docs/INNOVATION_PLAN_2026.md` I-17 (Wave 3) is explicitly scoped as the follow-up that "extends I-03's quantization awareness... Fit-to-memory logic (I-03) computes weights + KV at requested context instead of weights alone." Building KV-cache modeling now would duplicate that already-planned item, and would require fabricating a memory formula LAIR has no real per-model architecture data (layer count, hidden size) to ground — a wrong-in-the-unsafe-direction estimate here is worse than not estimating at all (ADR-0011's own reasoning). This ADR deliberately defers it.

---

# Decision

Quantization becomes an explained, scored routing dimension — on top of the fit enforcement that already existed — without touching the hard-filter safety property.

- **`ModelMetadata`** (`app/providers/model_metadata.py`) gains `is_moe: bool` and `active_params_b: float | None`. Detected heuristically from the model id's `-A<n>B` active-parameter suffix (`app/hardware/resource_resolver.detect_moe()`) — no provider exposes MoE-ness as real metadata yet, matching the same honesty ADR-0013 already established for REASONING/CODING/etc.
- **`ModelScorer`** gains a `quant_fit` factor (provenance `DECLARED`): when `ModelMetadata.quantization` is known, it adds `RoutingPolicy.quant_efficiency_weight` (default `2.0`) for a memory-efficient family (Q2/Q3/Q4) and `0.0` otherwise, with a reason string naming the quant and, when available, the estimated vs. free RAM (e.g. `"Q4_K_M selected, ~17.6GB estimated, 20.0GB free"`). This is a **tie-breaking preference among candidates that already passed `filter_by_hardware()`'s hard fit check** — it never overrides that filter and never claims a quant "fits" on its own authority.
- **MoE models** get an informational note in the same reason (`"(MoE, ~3B active params -- may fit better with expert-offload enabled in LM Studio)"`) but **no memory-estimate reduction**. LAIR doesn't control whether expert-offload is actually enabled in the backend; claiming a smaller footprint than what's really resident risks real OOM. The note is honest about being conditional, not a claim LAIR is making on the user's behalf.
- **`ModelScorer.score()`** gains optional `resource_profile`/`hardware` parameters so it can reference the same estimate and live hardware snapshot `filter_by_hardware()` already computed in `RoutingEngine.route()`, threaded through `ModelSelector.select()` — no second hardware detection path, no drift between what filtered a candidate and what the explanation says about it.
- **KV-cache-aware memory fit stays out of scope for this ADR**, per I-17's explicit follow-up scoping described above.

---

# Alternatives Considered

## Build KV-Cache-Aware Memory Estimation Now

Cons

- No real per-model architecture data (layer count, hidden size) exists anywhere in LAIR to ground a formula; a plausible-looking but uncalibrated number is worse than the current honest "weights only" estimate
- `docs/INNOVATION_PLAN_2026.md` already scopes this as I-17's job specifically because it builds on this ADR's quant-fit explanation — building it here duplicates a planned item instead of sequencing after it

## Reduce the Memory Estimate for MoE/Expert-Offload Models

Cons

- LAIR has no request-time control over whether LM Studio's expert-offload is actually enabled for a given load; assuming it is and shrinking the estimate accordingly could pass a model through the hard filter that then fails to load or thrashes -- the same "wrong rejection is worse than a missed one, but a wrong acceptance is worse still for a hard constraint" reasoning ADR-0012 already established

## Introduce a Static `configs/registry.yaml` Listing Every Quant Variant Explicitly

Cons

- Duplicates the live provider list (ADR-0002) as a second, driftable source of truth for what's actually downloaded and loaded -- LM Studio's `ModelMetadata.quantization` per discovered model already gives LAIR everything this pass needs without inventing new state to keep in sync

---

# Consequences

Benefits

- Routing explanations now name the quant chosen and why, closing the gap I-13's provenance work made visible (a `quant_fit` factor existed nowhere to tag)
- A bigger model at an efficient quant can now win a tie against a smaller model at an inefficient one, when both already fit -- the actual "prefer larger-Q4 over smaller-Q8" preference I-03 asked for
- MoE models are surfaced informationally without LAIR overclaiming a memory benefit it can't verify it's actually getting

Trade-offs

- The efficiency bonus is a flat preference (Q2/Q3/Q4 vs. everything else), not a graded one -- Q5/Q6 sit in the same bucket as Q8/F16 for now; a finer scale can be added if real usage shows it matters
- Memory fit is still weights-only; a long conversation's KV cache can still be the actual thing that runs a machine out of memory even after this pass -- explicitly I-17's job next, not silently fixed here

---

# Decision Summary

LAIR now explains and softly prefers quantization choices on top of the hard memory-fit filter that already existed, without fabricating precision (KV-cache sizing, MoE memory reduction) it has no real data to back -- both stay honestly deferred to I-17 and to actual expert-offload support, respectively.
