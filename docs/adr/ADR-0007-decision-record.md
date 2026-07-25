# ADR-0007 — DecisionRecord

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

The Learning Engine, Benchmark Engine, a future dashboard, and explainability all need a canonical trace of what LAIR decided and why.

Without one shared artifact, each subsystem risks building its own private log, causing drift between what is logged for training and what is shown to users. Retrofitting a canonical shape after those subsystems already depend on divergent logs is closer to a data migration than a refactor.

---

# Decision

LAIR introduces `DecisionRecord` as the single, immutable artifact produced by every Decision Engine resolution.

A DecisionRecord captures:

- The DecisionProblem considered (Task, Intent, Objective, Constraints, Requirements)
- The full candidate set and each candidate's raw per-signal scores
- The RoutingPolicy version applied
- The KnowledgeBase snapshot version consulted
- The chosen ExecutionStrategy
- A timestamp

Explanation is generated from DecisionRecord as a pure projection. It is never maintained independently.

Every downstream consumer — Learning Engine, Benchmark Engine, dashboard, audit log — reads DecisionRecord. None reads raw scorer output directly.

---

# Alternatives Considered

## Independent Per-Subsystem Logging

Pros

- No shared schema to agree on upfront

Cons

- Duplicated logic for explanation generation
- Drift between training data and user-facing explanations
- No single place to answer "why did LAIR choose this model on this date"

## Reuse RoutingDecision as the Canonical Record

Cons

- No versioning of policy or knowledge
- No representation of rejected candidates
- Tied to a single-model shape the Execution Planner will outgrow

---

# Consequences

Benefits

- One artifact for explainability, audit and learning
- Decisions become reproducible: policy and knowledge versions are captured
- Adding a new scoring signal requires changing the record's schema, not every consumer

Trade-offs

- Every Decision Engine resolution produces a heavier object than today's ScoreBreakdown
- Requires a persistence decision (even lightweight structured logs) before Benchmark Engine work begins

---

# Decision Summary

Every decision LAIR makes produces exactly one durable record. Explanations, training data and audit trails are derived from it, never a separate source of truth.
