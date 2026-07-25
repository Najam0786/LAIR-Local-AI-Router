# ADR-0008 — RoutingPolicy

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

Scoring weights currently live in three uncoordinated places:

- `app/core/settings.py` (`STREAMING_WEIGHT`, `CAPABILITY_WEIGHT`, `CONTEXT_WINDOW_WEIGHT`)
- `app/routing/capability_weights.py` (`CAPABILITY_WEIGHTS`, per CapabilityType)
- `CapabilityRequirement.weight` (per request)

Benchmark Engine, Objective-driven scoring and Learning Engine will each need to read, and eventually write, weights. This three-way split has no single owner and will not survive those additions.

---

# Decision

LAIR introduces `RoutingPolicy` as the single source of scoring weights and priorities (capability weight, benchmark weight, latency weight, hardware weight, provider weight, ...).

Every scorer (CapabilityScorer, BenchmarkScorer, HardwareScorer, LatencyScorer, ProviderScorer) reads its weight from RoutingPolicy and computes only its own signal. No scorer owns a weight constant.

RoutingPolicy is versioned. The active version is captured in every DecisionRecord. The Learning Engine, when introduced, writes new RoutingPolicy versions — it never mutates scorers directly.

---

# Alternatives Considered

## Keep Weights in Settings

Pros

- Minimal change today

Cons

- Conflates deployment configuration (host, port) with routing policy
- No versioning
- No path for per-request or per-Objective overrides

## Let Each Scorer Own Its Weight

Cons

- No single place to answer "why does the system currently favor reasoning over latency"
- Blocks future Objective-driven policy selection

---

# Consequences

Benefits

- One place to change routing behavior
- Supports future per-Objective policy selection and Learning-Engine-driven adaptation without touching scorer code
- Every decision is auditable against a specific policy version

Trade-offs

- `STREAMING_WEIGHT`, `CAPABILITY_WEIGHT`, `CONTEXT_WINDOW_WEIGHT` and `CAPABILITY_WEIGHTS` become migration work, not additive work, once RoutingPolicy exists

---

# Decision Summary

Weights belong to RoutingPolicy — not Settings, not individual scorers, not individual requests. Every scorer reads the same policy, and every policy version is traceable.
