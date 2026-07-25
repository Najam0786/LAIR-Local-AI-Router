# ADR-0018 — Hybrid Cloud Escalation

**Status:** Accepted

**Date:** 2026-07-25

---

# Context

RFC-0001 proposed an optional, budget-capped cloud escalation path, gated on CLAUDE.md's constraint #1: never send a prompt to a cloud API unless the feature is explicitly enabled *and* within budget. This ADR records the concrete implementation decisions the RFC left to implementation time.

---

# Decision

- **`BaseProvider.is_cloud: bool = False`** (ADR-0002 unchanged otherwise) lets escalation logic identify a cloud provider generically. `OpenAICompatibleCloudProvider` (`app/providers/cloud.py`) sets it `True`, implements `BaseProvider` unchanged, and is inert (safe no-op) whenever no API key is configured -- constructing it unconditionally at import time is safe.
- **`CloudBudgetLedger`** (`app/costs/budget.py`) is a genuinely separate store from `SavingsLedger` (I-01), same JSON-backed pattern. Its monthly budget is either fixed at construction (for tests/DI) or read live from `Settings.CLOUD_MONTHLY_BUDGET_USD` on every check when not given explicitly -- a real bug surfaced during this implementation's own tests: a ledger constructed once (e.g. by an autouse test fixture) before the budget is configured must still see later configuration, not a stale snapshot from before the caller set it up.
- **Escalation lives entirely at the API layer** (`app/api/chat.py`), not inside `RoutingEngine.route()`: `evaluate_escalation()` (`app/routing/cloud_escalation.py`) runs *after* the normal local routing decision, using its `complexity` and `confidence` as two of its three required signals. This keeps the routing engine exactly as pure as I-04 Phase 2 already required (it never performs inference, only decides who does) -- cloud escalation is a decision *about* a completed local routing decision, not part of making one.
- **The gate requires three independent conditions together**: complexity at/above `CLOUD_ESCALATION_COMPLEXITY_THRESHOLD`, local confidence below `CLOUD_ESCALATION_LOCAL_CONFIDENCE_THRESHOLD`, and a conservative cost estimate that fits `CloudBudgetLedger.remaining_this_month()` -- checked *before* the call goes out. Any one condition failing keeps the request local.
- **`CloudEscalator.execute()`** mirrors `app.execution.runtime.execute()`'s never-raises contract exactly: a failed cloud call becomes a failed `ExecutionOutcome`, and the API layer falls through to normal local execution -- cloud escalation failure is never a hard failure of the request.
- **Real spend is recorded only after a successful cloud call**, from actual returned token usage (`CloudEscalator.actual_cost_usd()`), not the pre-call estimate -- the estimate exists solely to gate whether to attempt the call.
- **Non-streaming only for this pass**, mirroring I-07/I-09's identical scoping decision -- streaming cloud escalation is real future work, not built speculatively.
- **No `DecisionRecord` is persisted for an escalated response.** `DecisionRecord.selected_model` and its scoring machinery are built around a routed local `AIModel`; force-fitting a cloud completion into that shape risked corrupting an invariant other code (the future Learning Engine, audit tooling) may come to rely on. Cloud escalation audit trail is `lair_meta.routed_to_cloud` / `cloud_escalation_reason` on the response itself for now -- decision-repository integration for the cloud path is flagged as follow-up, not silently faked.

---

# Alternatives Considered

See RFC-0001's Alternatives Considered -- unchanged by implementation. One additional implementation-time alternative:

## Persist a Synthetic `DecisionRecord` for Escalated Responses

Cons

- `DecisionRecord.candidates`/`ScoredCandidate` are built entirely around `ModelScorer`'s local scoring pipeline; a cloud completion has no real `ScoreBreakdown` to report honestly -- fabricating one to satisfy the schema would misrepresent how the decision was actually made

---

# Consequences

Benefits

- The routing engine's purity guarantee (no inference inside `RoutingEngine.route()`) extends cleanly to cloud escalation without special-casing
- A three-condition gate makes an accidental cloud call from a single bad signal (e.g. a triage false positive) very unlikely
- The live-settings budget fix applies beyond tests: a deployment that changes `CLOUD_MONTHLY_BUDGET_USD` at runtime (env reload, admin action) takes effect immediately rather than requiring a ledger object to be reconstructed

Trade-offs

- Escalated responses aren't yet part of the same audit trail (`logs/decisions.json`) as local ones -- a real gap for anyone auditing all traffic uniformly, explicitly deferred rather than solved with a synthetic record
- Streaming requests never escalate, even when they'd otherwise qualify -- a real capability gap, not a silent one (the request just proceeds locally)

---

# Decision Summary

Cloud escalation is implemented as a post-routing API-layer decision, gated on three independent signals plus a live-checked budget, with real spend recorded only after success and every response transparently marked -- keeping RoutingEngine's no-inference purity guarantee intact and never claiming an audit-trail integration this pass doesn't actually have.
