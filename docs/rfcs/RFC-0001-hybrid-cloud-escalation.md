# RFC-0001 — Hybrid Cloud Escalation

**Status:** Accepted

**Date:** 2026-07-25

---

## Summary

An optional, hard-budget-capped escalation path to cloud LLM APIs (OpenAI-compatible first), used only when a request genuinely exceeds local capability and the feature has been explicitly enabled with a nonzero budget. Off by default. Every cloud-routed response is transparently marked.

---

## Motivation

`docs/INNOVATION_PLAN_2026.md`'s Mission A frames cloud usage as "a tightly budgeted exception, not the default" — LAIR should let a user do 90%+ of their AI work locally, with cloud as a deliberate, bounded escalation for the genuinely hard remainder, not an all-or-nothing choice. Section 1.6's research finding backs this: real-world hybrid setups see 60-83% cost reduction by routing high-volume easy traffic locally and reserving cloud for hard tasks, not by avoiding cloud entirely.

Today, a request LAIR's local models handle poorly (complexity 5, a task type no local model is good at, a context window overflow) still gets routed to the best available local model regardless — there's no alternative, even for a user willing to pay a small, bounded amount for a better answer on the rare hard case.

---

## Background

**Current behavior.** `RoutingEngine.route()` only ever sees local providers (LM Studio today). `BaseProvider` (ADR-0002) is already provider-agnostic — nothing about it assumes "local" — but no cloud provider has ever been registered, and `provider_registry` has no concept of a provider being conditionally available.

**Existing limitation.** CLAUDE.md's constraint #1 is explicit: "never send user prompts to any cloud API unless the hybrid-routing feature is explicitly enabled AND within the user's budget cap" (AND, not OR — both conditions, always). No budget-tracking mechanism exists yet. I-01's `SavingsLedger` tracks money *not* spent (cloud-equivalent cost avoided by routing locally) — a different, incompatible concept from money *actually* spent against a hard cap; reusing it for both would conflate an informational, always-non-negative running total with a limit that must never be silently exceeded.

---

## Proposal

- **Cloud providers implement the existing `BaseProvider` interface unchanged** (ADR-0002) — e.g. a first `OpenAICompatibleCloudProvider` for any OpenAI-compatible cloud endpoint. Each cloud provider class carries `is_cloud: bool = True`, letting routing special-case it without a provider-registry redesign.
- **Never auto-registered.** A cloud provider is only registered when *both* `Settings.ENABLE_CLOUD_ESCALATION` is `True` *and* a valid API key is configured for it. No key, no registration — the provider simply doesn't exist as far as routing is concerned, the same "unconfigured means absent, not degraded" pattern I-04 Phase 2 and I-09's summarizer already use.
- **A new `CloudBudgetLedger`** (`app/costs/budget.py`), separate from `SavingsLedger`: tracks real spend against `Settings.CLOUD_MONTHLY_BUDGET_USD`, JSON-backed in the same pattern as every other store in this codebase (`KnowledgeBase`/`DecisionRepository`/`SavingsLedger`/`ResponseCache`). Exposes `remaining_this_month() -> float`.
- **Escalation is a gate, not a scored preference.** Cloud candidates are only considered when: (a) the feature is enabled, (b) the budget has headroom, and (c) a real trigger fires — complexity ≥ the configured threshold *and* the best local candidate's score/confidence is low, or local capability filtering leaves zero viable candidates, or the requested context exceeds every local model's context window. This matches the "pre-route only clearly-hard queries directly to the strong tier, cascade only the ambiguous middle" pattern research section 1.4 describes, and mirrors ADR-0012's own reasoning for why hardware fit is a hard filter rather than a score: something this consequential shouldn't be reachable by an ordinary scoring-weight misconfiguration.
- **Budget checked before the call, conservatively.** Estimated cost (from request size, using the existing `configs/cloud_pricing.yaml` machinery) must fit within remaining budget *before* the request is sent; a request that would plausibly exceed the cap doesn't go out, it falls back to best-effort local.
- **Total transparency.** Every cloud-routed response carries `lair_meta.routed_to_cloud=true` and a `reason`; the fact that a prompt left the machine is never silent.
- **Budget exhaustion degrades gracefully.** Falls back to the best local candidate with an honest note in `lair_meta` — never a hard failure just because the cloud tier was unavailable.

---

## Alternatives Considered

**Cloud as an always-present scored candidate.** Rejected: lets a scoring-weight bug or misconfiguration route to the cloud on an ordinary request without the user ever explicitly deciding that should happen — too consequential (real money, real data leaving the machine) to be reachable by anything softer than an explicit gate.

**Reuse `SavingsLedger` for budget tracking.** Rejected: "money not spent" (informational, always non-negative, I-01) and "money actually spent against a hard cap" (must never silently exceed a limit, I-06) are different enough concepts that sharing one object risks a bug in one corrupting the other's meaning.

**Cascade with local self-verification before escalating (AutoMix-style: answer locally first, escalate only if a verifier judges it insufficient).** Deferred, not rejected: doubles local inference cost on every single request just to decide whether to escalate. The simpler "pre-route obviously-hard, no cascade" heuristic is a reasonable first cut; self-verification is real future work once there's evidence on how accurate I-04's complexity triage actually is in practice (ties to the still-open "Router Decision Accuracy measurement" item in this project's history).

---

## Benefits

- Genuinely hard tasks get a real answer instead of the best-available (possibly poor) local one, without abandoning local-first for the ~90%+ of traffic that doesn't need it
- A hard budget cap makes the feature safe to enable and forget
- Transparent by construction — matches LAIR's explainability principle rather than being a silent fallback

---

## Risks

**Privacy.** A prompt leaving the machine is a real trust-boundary crossing. Mitigated by opt-in-only, per-response marking, and the fact that escalation only fires on an explicit trigger, never by default. A future per-request "never escalate this" flag (mirroring I-07's `lair_no_cache`) is flagged as follow-up work, not built speculatively ahead of real demand.

**Cost-estimation error before the call completes.** Mitigated by checking a conservative (upper-bound) estimate against remaining budget before sending, not an exact figure computed only after the response returns.

**Credential handling.** Cloud API keys are real secrets — sourced from `Settings`/environment only, never logged, never accepted from a request payload.

**Complexity-triage false positives.** Mitigated by requiring complexity *and* a local-quality signal together, not complexity alone, as an escalation trigger.

---

## Dependencies

- `httpx` (already a dependency) for cloud API calls
- I-01's `PricingTable`/`configs/cloud_pricing.yaml`, extended for a second purpose (real spend, not avoided-cost estimation) — not replaced
- I-04's complexity triage as one escalation-trigger input
- ADR-0002 (Provider Abstraction) — cloud providers implement `BaseProvider` unchanged
- A new ADR (written alongside implementation) covering the provider registration model, budget ledger schema, and exact escalation-trigger logic

---

## Success Criteria

- Cloud providers configurable via env/settings; registered only when both `ENABLE_CLOUD_ESCALATION` and a valid API key are present
- Hard cap enforced, with tests simulating cap exhaustion mid-month; no single request can push spend past the cap
- Every cloud-routed response carries `lair_meta.routed_to_cloud=true` and a reason
- With the feature disabled (the default), behavior is byte-identical to pre-RFC-0001 LAIR

---

## Future Work

- Cascade with local self-verification (AutoMix-style) once real triage-accuracy evidence exists
- Per-request sensitive-content exclusion from escalation
- Multiple cloud providers with price/quality-aware selection among them (this RFC: first configured provider with budget headroom, not a multi-provider auction)
