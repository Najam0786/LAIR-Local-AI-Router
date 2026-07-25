# ADR-0005 — Benchmark-Driven Routing

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

Capability-based routing (ADR-0004) matches models against requirements, but scores them using static, heuristic weights. Two models that both claim `REASONING` are scored identically regardless of how fast either one actually is on the hardware LAIR is running on.

The project's mission statement itself frames this as unfinished: "benchmark-driven" routing was a stated goal from the beginning, not something added later.

---

# Decision

LAIR introduces a Benchmark Engine that measures real model performance and feeds it into routing.

Scope for this first version is deliberately narrow: **latency and throughput only**. No quality/accuracy scoring, no eval dataset, no judge model — those require infrastructure (eval sets, scoring rubrics) that doesn't exist yet and would be speculative to build ahead of need.

- `BenchmarkRunner` calls each model through the existing `BaseProvider.complete()` contract — never bypasses the provider abstraction — and measures wall-clock latency and tokens/sec. Runs sequentially, not concurrently: parallel calls against one local inference server would make each model's latency include queueing from the others, corrupting the measurement.
- A failing model (unreachable, not actually loaded, wrong endpoint) is logged and skipped; one bad model never aborts the whole run.
- `KnowledgeBase` stores every result, JSON-file-backed for now. It is read-only from the Decision Engine's side — only the Benchmark Engine (and, later, the Learning Engine and provider health monitors) writes to it.
- `RoutingPolicy.benchmark_weight` and `ScoreBreakdown.benchmark_score` feed measured throughput into the existing scoring formula as one more additive term, alongside capability, streaming, and context-window scores.

---

# Alternatives Considered

## Quality/Accuracy Scoring in v1

Cons

- Requires an eval dataset and a scoring method (keyword match, judge model) that don't exist yet
- Conflates two different, independently useful signals (is it fast vs. is it good) into one milestone

## Concurrent Benchmark Execution

Cons

- Measures contention, not the model's real standalone performance
- Non-deterministic, harder to reproduce and compare across runs

---

# Consequences

Benefits

- Routing decisions are backed by measured evidence, not just static heuristics
- New scoring dimensions (quality, memory, reliability) can be added the same way later, without redesigning the pipeline
- Graceful per-model failure means one misconfigured or unloaded model doesn't take down benchmarking for the rest

Trade-offs

- `benchmark_score` is 0 for any model with no recorded benchmark — routing still falls back entirely to capability/streaming/context scoring until a model has been measured at least once
- JSON-file storage is not multi-process safe and doesn't yet distinguish between providers serving models with the same id — acceptable for the current single-provider, single-process scope

---

# Decision Summary

LAIR routes using measured throughput, not just claimed capability — and the Benchmark Engine that produces those measurements sits entirely outside the Decision Engine, feeding it evidence rather than participating in the decision itself.
