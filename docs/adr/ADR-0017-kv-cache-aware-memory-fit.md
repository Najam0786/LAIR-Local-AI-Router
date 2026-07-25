# ADR-0017 — KV-Cache-Aware Memory Fit

**Status:** Accepted

**Date:** 2026-07-25

---

# Context

ADR-0016 (I-03) explicitly deferred KV-cache-aware memory estimation: "no real per-model architecture data (layer count, hidden size) exists anywhere in LAIR to ground a formula... `docs/INNOVATION_PLAN_2026.md` already scopes this as I-17's job." This ADR is that follow-up.

Until now, `filter_by_hardware()`'s hard fit check (ADR-0012) and `ModelScorer`'s quant explanation (ADR-0016) both used `ResourceProfile.estimated_ram_gb` — a **weights-only** estimate. That's a real gap: `docs/DOGFOODING.md` DF-006 point 3 already documented a live failure of exactly this shape — LM Studio's "Default Context Length: Model maximum" setting reserved KV cache for a model's *entire* max context, ballooning the real memory requirement to 33+GB on a 32GB machine, for a model whose weights alone would have fit comfortably. A weights-only fit check cannot catch that class of failure; it isn't hypothetical, it already happened on this project's reference machine.

The blocker in ADR-0016 remains real: LAIR has no per-model layer count or hidden size anywhere. This ADR resolves it not by acquiring that data, but by using a **calibrated, deliberately conservative constant** instead of per-architecture precision.

---

# Decision

`ResourceProfile` gains `estimated_kv_cache_gb`, `estimated_total_ram_gb`, and `kv_cache_quant_recommended`, plus an `effective_ram_gb` property (weights+KV total when known, falling back to weights-only — so every existing caller that never populates the new fields keeps working exactly as before this ADR).

- **The KV-cache formula is calibrated from Llama-2-7B's real, published architecture** (32 layers, hidden size 4096, standard multi-head attention, fp16): `2 (K and V) × 32 × 4096 × 2 bytes = 524,288 bytes/token`, or `~74,898 bytes/token/billion-params`. This is a real reference point, not an invented number.
- **It's used as a deliberate upper bound, not a measurement.** Most of LAIR's actual portfolio (Qwen, Gemma, DeepSeek) uses grouped-query attention, which needs meaningfully less KV cache per token than the MHA architecture this constant is calibrated from. Real usage should fit at least as well as this predicts, never worse — the same "a wrong rejection is worse than a missed one, but a wrong acceptance is worse still for a hard constraint" reasoning ADR-0011/ADR-0012 already established, applied in the safe direction: overestimating a hard memory constraint, not underestimating it.
- **`ResourceResolver.resolve()`** gains optional `context_window` (the model's currently-configured context length, from `ModelMetadata`/`CapabilityProfile` — real provider-reported data per ADR-0013, not a guess) and `available_ram_gb` parameters. When both are given, it also computes `kv_cache_quant_recommended`: the least-lossy KV precision (fp16/int8/q4, at 1x/0.5x/0.25x the fp16 byte cost) that would let weights+KV fit.
- **`filter_by_hardware()`** now checks `effective_ram_gb` instead of `estimated_ram_gb` — the hard fit constraint now genuinely accounts for KV cache at the model's real configured context, closing the DF-006 gap.
- **`ModelScorer`'s existing `quant_fit` explanation factor (ADR-0016)** is extended, not duplicated: it now names the KV cache estimate and, when reduced precision is needed, recommends it (e.g. `"Q4_K_M selected, ~17.6GB estimated, ~18.3GB fp16 KV cache at full context -- recommend int8 KV cache in LM Studio..."`).
- **This is a recommendation, not a remote setting.** `docs/INNOVATION_PLAN_2026.md` I-17 asks that "where the backend exposes KV quant settings, LAIR sets them per request/model" — unlike `ttl` and `draft_model` (confirmed real LM Studio request-payload fields, section 1.3 of the plan), no verified LM Studio request-level API exposes KV-cache precision per request. LAIR does not fabricate a payload field that might silently be ignored; the recommendation is surfaced in the explanation for the user to apply in LM Studio's own load settings.
- **Portfolio files** (`configs/portfolios/{tier}.yaml`) gain `kv_cache_recommendation` (`fp16`/`int8`): `int8` for ENTRY/CPU_ONLY (matching the plan's own "on ≤8GB machines LAIR can choose int8 KV to double usable context"), `fp16` for STANDARD/ENTHUSIAST where headroom is ample.

---

# Alternatives Considered

## Wait for Real Per-Architecture Metadata Before Building Anything

Cons

- No provider (LM Studio included) exposes layer count/hidden size today, and there's no evidence one will soon — waiting indefinitely leaves the real, already-observed DF-006 failure mode uncaught
- A calibrated, explicitly-conservative constant is honest about what it is (an upper-bound heuristic, documented as such) in a way "wait for perfect data" doesn't actually improve on for the safety property that matters (never underestimate a hard constraint)

## Derive Per-Architecture Parameters from Total Parameter Count via a Fitted Curve

Cons

- Would require curve-fitting against multiple real architectures to calibrate confidently; LAIR has exactly one grounded reference point (Llama-2-7B) today, not enough to fit a curve without fabricating additional data points
- A single conservative constant, honestly labeled as an upper bound, is more defensible than false precision from an under-supported fit

## Fabricate a `kv_cache_quant` Request Payload Field for LM Studio

Cons

- No verified documentation confirms LM Studio's `/v1/chat/completions` accepts a per-request KV-cache-precision field the way it does for `ttl` (confirmed) or `draft_model` (confirmed, section 1.3 of the plan) -- sending an unverified field either does nothing silently or, worse, could be misinterpreted; recommending the setting for the user to apply in LM Studio's own UI is the honest choice until such an API is confirmed

---

# Consequences

Benefits

- Closes a real, already-documented failure mode (DF-006 point 3) at the fit-check level instead of leaving it to LM Studio's own guardrails to catch (or not) at load time
- Routing explanations now name a concrete, actionable KV-cache recommendation instead of staying silent on a real memory driver
- Portfolio recommendations are now context-length-aware per tier, not just model-size-aware

Trade-offs

- The calibration constant is a real but single reference point (Llama-2-7B, MHA) applied uniformly across architecturally different models (mostly GQA) -- conservative in the safe direction, but not a per-model measurement, and will overestimate GQA models' real KV cache noticeably
- LAIR cannot actually configure the backend's KV precision -- only recommend it in the explanation, leaving a manual step for the user
- `filter_by_hardware()` is now stricter than before this ADR for any model with a known context window, which could reject a candidate that would have passed under the old weights-only check -- the intended, safety-motivated effect, not a regression

---

# Decision Summary

LAIR now accounts for KV cache in its hard memory-fit check and routing explanations, using a calibrated-but-conservative constant grounded in one real published architecture rather than either fabricated precision or an indefinite wait for per-model data that doesn't exist -- and recommends, but does not claim to remotely set, the backend KV precision that would let a model's full context fit.
