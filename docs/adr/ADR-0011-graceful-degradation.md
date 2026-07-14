# ADR-0011 — Graceful Degradation

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

The same shape of decision has now appeared independently three times:

- `BenchmarkRunner` — a model fails to respond (unreachable, not actually loaded, wrong endpoint): log a warning and skip it, rather than aborting the entire benchmark run.
- `KnowledgeBase` — a stored record fails to parse (e.g. it predates a schema change): log a warning and skip it, rather than crashing whatever asked for benchmark data.
- The Decision Engine — no model satisfies a request's requirements: this is treated as an expected business outcome (`NoCandidateModelsError`, mapped to a 404), not an unexpected failure.

These weren't designed together as one mechanism. They converged independently because the same underlying rule applies each time.

---

# Decision

LAIR treats the partial or expected failure of one unit of work as something to skip and continue past, not something to crash on — as long as the failure is scoped to that one unit and doesn't compromise the correctness of what still succeeds.

This applies at two levels:

- **Per-item, within a batch.** One model failing during a benchmark run, or one unreadable record in the KnowledgeBase, does not invalidate the other items being processed. Log and continue.
- **Expected vs. unexpected conditions get different exception types.** "No candidate model satisfies this request" is a named, specific exception (`NoCandidateModelsError`), not a bare `ValueError` — so it can be caught precisely without accidentally swallowing an unrelated bug that happens to also raise `ValueError` (as `pydantic.ValidationError` does).

This is not blanket exception suppression. A failure is only swallowed when: (a) it's scoped to one item in a larger batch, and (b) skipping that item is a safe, correct thing to do (the rest of the batch is still valid). A failure that would compromise the correctness of the whole operation should still propagate.

---

# Alternatives Considered

## Fail the Whole Batch on Any Item's Failure

Cons

- One unreachable or unloaded model would make it impossible to benchmark any of the others
- One legacy/malformed stored record would make `/route` unusable until the data file is manually cleaned up

## Catch Bare `Exception`/`ValueError` Everywhere by Convention

Cons

- Already caused a real bug: catching bare `ValueError` in the API layer mislabeled an unrelated `pydantic.ValidationError` as "no suitable model found," hiding the actual problem during debugging

---

# Consequences

Benefits

- One bad model, one bad record, or one unsatisfiable request no longer takes down anything beyond itself
- Naming the expected-failure exception types explicitly (`NoCandidateModelsError`) keeps broad `except` blocks from accidentally catching bugs they weren't meant to catch
- Establishes a convention future code should follow: skip-and-continue for per-item batch failures, named exceptions for expected business outcomes

Trade-offs

- Skipped items are only visible via logs today — there's no user-facing surfacing of "2 of 6 models were skipped" beyond what `scripts/run_benchmarks.py` prints to stdout. Acceptable at current scale; worth revisiting if silent skips ever hide a real, ongoing problem rather than an expected one.

---

# Decision Summary

A failure scoped to one item in a batch is skipped and logged, not escalated; an expected "no answer" business outcome gets its own exception type, not a bare built-in one. Three independent parts of the codebase already converged on this rule — this ADR just writes it down so the next one does too.
