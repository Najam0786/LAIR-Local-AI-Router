# ADR-0010 — Decision Persistence

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

Every `/route` call already builds a `DecisionRecord` (ADR-0007) — the full candidate list, the policy applied, and the selected model. Until now it was discarded the moment the HTTP response was sent.

A future Learning Engine needs historical decisions to learn from. Without persistence, that phase has no data to work with when it eventually arrives.

---

# Decision

LAIR introduces `DecisionRepository`, an append-only store of every `DecisionRecord`, written by the Decision Engine immediately after a decision is made.

- JSON-file-backed for now (`logs/decisions.json`), following the exact pattern already established by `KnowledgeBase`.
- Written only by the Decision Engine (`RoutingEngine.route()`). Read only by future consumers — the Learning Engine, audit tooling, a dashboard — never by the Decision Engine itself. Same one-way CQRS shape as `KnowledgeBase`.
- No "latest per key" lookup, unlike `KnowledgeBase` — this is a plain append-only log, not a per-model table.

Two related ideas were considered and deliberately deferred:

- **A full versioned `KnowledgeSnapshot` object** (generated-by, benchmark version, policy version, explicit snapshot boundaries) — no concrete consumer needs this yet. Instead, `BenchmarkRunner.run()` now stamps a lightweight `run_id` onto every `BenchmarkResult` it produces in one call, which is enough to group results by run without building a separate versioning subsystem ahead of need.
- **A formal storage-adapter abstraction** over `KnowledgeBase`/`DecisionRepository` (explicit interface for JSON vs. SQLite vs. Postgres backends) — both classes already sit behind a small, stable interface (`record`/`all` or `record`/`latest`/`all_latest`); that interface is the seam a future backend would need. Building a formal adapter layer before a second backend actually exists would be premature.

---

# Alternatives Considered

## No Persistence Until Learning Engine Needs It

Cons

- By the time Learning Engine starts, there's no historical data to bootstrap from — decisions made in the meantime are lost permanently, not deferred

## Full Versioned Snapshot Model Now

Cons

- No concrete consumer exists yet to validate the design against
- Risks over-designing a schema that gets revised anyway once Learning Engine defines what it actually needs to read

---

# Consequences

Benefits

- Decision history starts accumulating now, not whenever Learning Engine happens to land
- Mirrors `KnowledgeBase`'s already-proven pattern exactly — no new architectural concept, just the same shape applied to a second kind of record
- `run_id` gives just enough grouping for future benchmark analysis without committing to an unproven versioning model

Trade-offs

- `logs/decisions.json` grows unbounded with no rotation or pruning yet — acceptable at current local, single-user scale
- Every `/route` call now does one additional synchronous file write — negligible at this scale, would need revisiting under real concurrent load

---

# Decision Summary

Every routing decision is now kept, not just returned — the Decision Engine writes to `DecisionRepository` the same way the Benchmark Engine writes to `KnowledgeBase`, and nothing downstream reads its own writes.
