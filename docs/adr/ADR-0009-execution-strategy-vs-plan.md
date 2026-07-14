# ADR-0009 — ExecutionStrategy vs ExecutionPlan

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

`RoutingDecision` currently assumes exactly one model per request.

LAIR's roadmap includes multi-model workflows — for example OCR, then chunk, then summarize, then merge, then verify — where a single Task requires more than one model invocation to produce one answer.

Conflating "the general approach chosen" with "the concrete steps for this request" into one object makes it hard to reason about either independently, and turns the eventual introduction of multi-step execution into a breaking change instead of an additive one.

---

# Decision

LAIR separates the general approach from its concrete instantiation.

- **ExecutionStrategy** — the kind of approach the Decision Engine chooses for a Task: single-model, chain, ensemble-vote, reject or clarify.
- **ExecutionPlan** — the concrete, resolved sequence of ExecutionSteps that instantiates the chosen ExecutionStrategy for one specific Task. Each step names a role, a model, a provider and its dependencies — empty or linear today, DAG-capable later.

The public `/route` API returns an ExecutionPlan-shaped response, a single-step plan today, rather than a flat `selected_model` string, so the arrival of multi-step strategies is additive to the response schema, not breaking.

---

# Alternatives Considered

## Extend RoutingDecision with Optional Multi-Model Fields

Cons

- Ambiguous whether a field represents the chosen approach or its instantiation
- Breaking API change when multi-step plans arrive, since `selected_model: str` cannot represent a sequence

## Introduce ExecutionPlan Only, Skip ExecutionStrategy

Cons

- No representation for the Decision Engine rejecting a Task or asking a clarifying question — those are not plans with steps
- Loses the Decision Engine's full decision space, as defined in ADR-0006

---

# Consequences

Benefits

- The Decision Engine's decision space (single-model, workflow, reject, clarify) is representable without overloading one type
- The API response shape survives the introduction of a real Planner without a breaking change
- ExecutionStrategy and ExecutionPlan mirror the RoutingPolicy/DecisionRecord relationship: general policy vs. specific instance

Trade-offs

- Two new types to maintain instead of one
- Every `/route` response is plan-shaped even when it is a single step, a small verbosity cost today for no functional gain until the Planner exists

---

# Decision Summary

The Decision Engine chooses a strategy; the execution layer resolves that strategy into a plan for one Task. Collapsing the two into one type would force a breaking API change the moment multi-step execution arrives.
