# RFC-0002 — Persistent Project Memory

**Status:** Accepted

**Date:** 2026-07-25

---

## Summary

A local, private, per-project memory store: LAIR extracts durable facts/preferences/decisions from chat exchanges, and injects the ones relevant to a new request as context — so a user doesn't re-explain their project every new chat or every tool switch. Off by default, fully local, fully transparent, and byte-identical to pre-RFC-0002 LAIR when disabled.

---

## Motivation

`docs/INNOVATION_PLAN_2026.md` §1.9 and I-18 name the core pain: every new chat, every tool switch, loses context. LAIR already sits between every client (VS Code, Cursor, a future voice interface) and every model — it is the natural single owner of continuity, rather than each client inventing its own. This is Mission A (daily usefulness drives adoption) and Mission B (small, targeted injections keep the cost low enough for an 8GB machine) solving each other, per the plan's own framing.

---

## Background

**Existing infrastructure this reuses, not duplicates.** I-07 (semantic cache) and I-08 (RAG-lite documents, ADR-0019) already established the pattern this needs: `EmbeddingModel` (`app/rag/embeddings.py`, `fastembed`, torch-free) for local vector embeddings, and a JSON-backed store + in-memory cosine-similarity retrieval (`DocumentStore`/`retrieve_relevant_chunks`) for "store once, retrieve the relevant slice at request time." I-18 is explicitly designed in the plan to reuse this machinery a third way, not reimplement it.

**What's new.** Nothing in LAIR today persists anything about *what a user has told it* across requests — `DecisionRepository` records routing decisions, not conversation content. I-18 is the first feature that durably stores prompt/response content, which is why it needs its own RFC (user-facing behavior + privacy posture) before an ADR (storage schema), per CLAUDE.md's workflow for privacy-relevant changes.

---

## Proposal

- **Storage: JSON-backed, not SQLite.** The plan's own design notes suggest "local SQLite + embedded vector index"; this RFC deviates and keeps the established pattern instead — every other store in this codebase (`KnowledgeBase`, `DecisionRepository`, `ResponseCache`, `DocumentStore`, `CloudBudgetLedger`) is a lock-guarded JSON file, and a single local user's project memory reaches nowhere near the scale where SQLite's transactional guarantees would matter. One storage idiom across the codebase beats introducing a second one for a use case that doesn't need it — the same reasoning ADR-0019 already applied to rejecting a vector database for RAG-lite.
- **Scoped, not global.** Memories belong to a `project_scope` (an opaque string the client provides — a repo path, a project name, anything stable) so a user's work on Project A never leaks into a request about Project B. `ChatCompletionRequest.lair_project_scope: str | None`, mirroring `lair_document_id`'s established opt-in pattern. No scope, no memory — the feature is invisible unless a client asks for it.
- **Off by default.** `Settings.ENABLE_PROJECT_MEMORY = False`. This is the most privacy-sensitive feature LAIR has ever shipped (durable storage of conversation content); it must be an explicit choice, not a silent default, matching CLAUDE.md's local-first posture and the conservative-default precedent `ENABLE_RESPONSE_CACHE` already set for anything that persists request content.
- **Extraction is heuristic, not model-assisted, in this pass.** A candidate memory is extracted from the user's message when it matches a small set of durable-statement patterns (explicit "remember...", "my name is...", "I prefer...", "I'm using...", "always/never...", "note that..."). This mirrors I-04's own two-phase precedent (cheap rules first, model-assisted later only once the cheap version proves insufficient) — it avoids a second inference call on every single exchange, keeping the feature's cost near zero when unused pieces don't fire.
- **Deduplication via embedding similarity**, not exact-text matching: a new candidate whose embedding is highly similar (cosine ≥ 0.92) to an existing memory in the same scope updates that memory's text and timestamp instead of creating a duplicate — the same "recency wins, don't accumulate near-duplicates" behavior a human would expect.
- **Retrieval budget grounded in the actually-selected model's real context window**, exactly like RAG-lite's `RAG_RETRIEVAL_TOKEN_BUDGET` (ADR-0019) — `min(Settings.MEMORY_TOKEN_BUDGET, context_window // 4)` — rather than the plan's suggested static per-hardware-tier table. The selected model's context window is a more precise, already-available-at-request-time signal than a coarse hardware tier, and avoids re-running hardware detection on every chat request just to look up a budget.
- **Full transparency.** `lair_meta.memory_injected_count` on every response tells the client how many memories were used (provenance `MEMORY`, the enum value I-13 already reserved for exactly this). `lair memory list/show/forget/export` CLI (mirroring `lair doctor`/`lair install`'s existing local-command pattern — no new HTTP surface needed for a single local user's own data) gives full read/delete/export access. Disabling the feature returns LAIR to byte-identical pre-RFC-0002 behavior.

---

## Alternatives Considered

**SQLite + embedded vector index (the plan's own suggestion).** Rejected for this pass: every existing store in the codebase is JSON-backed; introducing SQLite as a one-off would mean two persistence idioms for no scale-driven reason yet. Revisit if real usage shows JSON's full-file-rewrite-on-write pattern becoming a bottleneck — not a foreseeable risk at "one user's project memory" scale.

**Model-assisted extraction from turn one.** Deferred, not rejected, mirroring I-04 Phase 1/2: adds a real inference cost to every exchange for a benefit (better-quality extraction) not yet proven necessary. Ship the free heuristic version; promote to model-assisted only if dogfooding shows the heuristic missing too much.

**Global (unscoped) memory.** Rejected: conflates unrelated projects, and the plan is explicit that continuity is *per-project*, not a single undifferentiated blob.

**Auto-inferred scope (e.g., from the working directory a client reports).** Deferred: no client today reliably reports this, and guessing wrong silently leaks context across projects — a real correctness/privacy risk. An explicit, client-supplied scope is honest about what LAIR actually knows.

---

## Benefits

- Real continuity across sessions and across tools, without any cloud dependency or telemetry
- Reuses proven local-embedding infrastructure (I-07/I-08) — no new heavy dependency
- Fully inspectable and revocable by the user (`lair memory` CLI), consistent with LAIR's explainability principle
- Zero behavioral change for anyone who doesn't opt in

## Trade-offs

- Heuristic extraction will miss some real facts and occasionally capture noise — an accepted, documented limitation of Phase 1, not silently pretended away
- JSON-backed storage doesn't scale to a very large number of memories per scope; acceptable at today's expected usage (a single user's project notes), a real limit if that changes
- Deduplication by embedding similarity can occasionally merge two genuinely-different-but-similar statements; the newer one always wins the merge, which is the safer failure direction (staleness beats duplication for a "what does the user currently believe" store)

---

## Dependencies

- `app.rag.embeddings.EmbeddingModel` (I-08) — reused directly, not reimplemented
- I-13's `Provenance.MEMORY` enum value — already reserved for this exact purpose
- A new ADR (written alongside implementation) covering the storage schema and dedup/retrieval logic in detail

---

## Success Criteria

- Memories persist across server restarts and across two different clients pointed at the same `lair_project_scope`
- With `ENABLE_PROJECT_MEMORY` off (the default), behavior is byte-identical to pre-RFC-0002 LAIR
- `lair memory list/show/forget/export` works against the real local store
- Every response that used injected memory reports it in `lair_meta`

---

## Future Work

- Model-assisted extraction (promote from heuristic once evidence supports it)
- MCP exposure of LAIR memory for other agents (per the plan's own interop watch-list)
- Voice sessions (I-11) attaching to the same project scope
