# ADR-0013 — Provider Metadata Grounding

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

`CapabilityResolver` and `ResourceResolver` inferred everything from substrings in the model id — `"-vl" in model_id` for vision, `"32b" in model_id` combined with a single flat constant for memory. The resolvers themselves called this out as a temporary placeholder from the start (ADR-0004), meant to be replaced once real metadata existed — not made cleverer with more heuristics.

Investigating what's actually available before designing a replacement (the same discipline applied to Benchmark Engine and Hardware Profiler) surfaced that LM Studio exposes a native API (`GET /api/v0/models`) distinct from the OpenAI-compatible `/v1/models` endpoint LAIR had used since Milestone 1. It returns real, structured per-model data: `type` (`llm`/`vlm`/`embeddings`), `capabilities` (e.g. `tool_use`, when LM Studio reports it), `quantization`, `state` (`loaded`/`not-loaded`), and `max_context_length`.

This also surfaced two things unrelated to the resolver replacement itself:

- **A dormant bug.** `CapabilityProfile.context_window` has been `None` for every model since Milestone 1 — the old resolver never set it, and nothing else did either — meaning `ModelScorer.context_window_score` has contributed exactly `0.0` to every routing decision this entire project.
- **An explanation for a past mystery.** Two models returned HTTP 400 during Milestone 2's benchmark runs. `state` shows why: they simply weren't loaded into memory, not broken.

There is still no real signal anywhere for REASONING, CODING, TRANSLATION, or SUMMARIZATION — LM Studio doesn't expose anything like that. Those stay heuristic.

---

# Decision

LM Studio's native metadata grounds what it can; nothing is guessed where real data now exists.

- **`ModelMetadata`** (`app/providers/model_metadata.py`) is a provider-agnostic struct — `is_vision`, `is_embedding`, `supports_tool_use`, `context_window`, `quantization`, `loaded`. `LMStudioProvider` translates its native API response into this; `CapabilityResolver`/`ResourceResolver` never see LM Studio's raw field names. Any future provider (Ollama, vLLM) can populate the same struct however it obtains that data — the resolvers' contract doesn't change per provider.
- **`CapabilityResolver.resolve()`** gains an optional `metadata` parameter. When present, VISION/EMBEDDING/TOOL_USE and `context_window` come from it; REASONING/CODING/TRANSLATION/SUMMARIZATION remain substring-based regardless, since nothing grounds them yet. When absent, behavior is identical to before this ADR.
- **`ResourceResolver.resolve()`** gains an optional `metadata` parameter. Parameter count still comes from the model id (no other source exists), but the GB-per-billion-parameters figure now varies by `quantization` family when known, instead of one flat constant for every model.
- **`LMStudioProvider.list_models()`** tries the native endpoint first and falls back to the original `/v1/models` call with no metadata on failure (older LM Studio version, different OpenAI-compatible server) — graceful degradation, per ADR-0011, not a hard dependency on the native API existing.
- **Not-loaded models are excluded from candidates** in `RoutingEngine.route()`, a plain filter alongside the existing capability and hardware filters. This is justified by directly observed behavior — a completion request against a not-loaded model returned HTTP 400 twice already in this project — not a guess. It is a narrow "is this specific model ready" check, not a Provider Health subsystem; health history, priority, and failover all stay deferred to that future milestone.

---

# Alternatives Considered

## Replace the Resolver with Semantic Classification

Cons

- Adds real complexity (embedding calls, similarity computation, exemplar phrases) to solve a problem that turned out to already have a much simpler, more accurate answer: the provider already knows the answer for several capabilities and was just never asked

## Keep Heuristics, Just Add More Substring Rules

Cons

- This is explicitly what ADR-0004 and every subsequent review of this resolver said not to do — more regex doesn't fix a resolver that's fundamentally guessing when real data is available

## Let LM Studio-Specific Fields Flow Directly into the Resolvers

Cons

- Couples domain-level capability/resource resolution to one provider's API shape, breaking the provider-agnostic contract those resolvers are meant to have — a second provider with a differently-shaped API would need its own resolver logic instead of reusing this one

---

# Consequences

Benefits

- VISION, EMBEDDING, and TOOL_USE detection is now correct by construction for LM Studio instead of guessed
- The dormant `context_window` bug is fixed — `ModelScorer` finally has real context-window data to score against
- `ResourceResolver`'s estimates are measurably more accurate using real quantization data
- Routing can no longer be sent to a model that's listed but not actually loaded

Trade-offs

- REASONING/CODING/TRANSLATION/SUMMARIZATION are still guessed — this ADR narrows the heuristic surface, it doesn't eliminate it
- Only one model is typically loaded at a time on a local LM Studio setup, so the loaded-state filter makes `/route` effectively single-candidate most of the time on this kind of setup — an accurate reflection of reality, not an artificial restriction, but worth knowing going in
- The native endpoint is LM Studio-specific; a future provider without an equivalent falls back to `ModelMetadata()` defaults (i.e. today's heuristic-only behavior) automatically

---

# Decision Summary

Where a provider already knows the answer, LAIR uses it instead of guessing — and where no provider knows the answer yet, LAIR is honest about still guessing, rather than pretending otherwise.

---

# Update — Loaded-State Hard Filter Softened

The "not-loaded models are excluded from candidates" decision above was justified by direct evidence at the time: a request to an unloaded model returned a bare HTTP 400 twice, with no graceful handling anywhere downstream. Two things changed since:

1. **Milestone 6** added `ExecutionOutcome`/graceful failure handling — a failed provider call now becomes a clean `success=False` result and a proper error response, not a bare crash.
2. **Live dogfooding (DF-006, `docs/DOGFOODING.md`)** confirmed, via repeated direct experimentation against real LM Studio, that its JIT loading + Auto-Evict reliably loads an unloaded model and evicts the previous one on request — the exact case the hard filter was previously preventing from ever being attempted.

`RoutingEngine.route()` no longer excludes unloaded models from candidates. Instead, `ModelScorer` adds a soft `loaded_bonus_score` (`RoutingPolicy.loaded_bonus_weight`, default `5.0`) — an already-loaded model is preferred when candidates are otherwise close (avoiding needless swap latency), but a genuinely better-suited unloaded model can still win and trigger a JIT load. `filter_by_hardware()` was updated alongside this: an unloaded candidate's estimated RAM is now checked against available RAM *plus* whatever RAM currently-loaded models would release on eviction, not against available RAM alone — otherwise a valid swap would still be wrongly rejected as "won't fit."

The original hard-filter reasoning remains accurate as historical context for why it was the right call in Milestone 5, with the data available at the time. This update reflects new evidence superseding it, not a mistake in the original decision.
