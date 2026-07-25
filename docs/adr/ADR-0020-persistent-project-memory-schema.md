# ADR-0020 — Persistent Project Memory: Storage Schema

**Status:** Accepted

**Date:** 2026-07-25

---

# Context

RFC-0002 accepted the shape of I-18 (persistent, per-project, local memory). This ADR fixes the concrete storage schema and the extraction/dedup/retrieval mechanics, the way ADR-0019 did for RAG-lite after RFC-0001's sibling process for I-06.

---

# Decision

- **`MemoryRecord`** (`app/memory/store.py`): `memory_id` (uuid4 hex), `project_scope` (str), `text` (the extracted statement), `embedding` (`list[float]`, via `EmbeddingModel`), `created_at`, `updated_at` (both UTC datetimes) — `updated_at` changes on a dedup-merge, `created_at` never does, so the record's age is always honestly answerable.
- **`MemoryStore`** (JSON-backed, lock-guarded, `logs/project_memory.json` default) — same shape as `DocumentStore`: `remember(project_scope, text, embedding) -> MemoryRecord`, `list_for_scope(project_scope) -> list[MemoryRecordInfo]` (metadata only, no embeddings, mirroring `DocumentInfo`), `forget(memory_id) -> bool`, `forget_all(project_scope) -> int` (count removed), `export_scope(project_scope) -> list[dict]` (full records, embeddings included, for `lair memory export`).
- **Dedup happens inside `remember()`**: before appending, compute cosine similarity between the new embedding and every existing record's embedding *in the same scope only* (never across scopes — a match in a different project is a coincidence, not the same fact). If the best match's similarity is ≥ `Settings.MEMORY_DEDUP_SIMILARITY_THRESHOLD` (default `0.92`), that record's `text`/`embedding`/`updated_at` are overwritten in place instead of a new record being appended.
- **Extraction** (`app/memory/extraction.py`): `extract_candidate_memory(message: str) -> str | None`, a small, fully-tested set of case-insensitive trigger patterns (`remember`, `my name is`, `i prefer`, `i'm using` / `i am using`, `always`, `never`, `note that`, `important:`). Returns the original message text verbatim when a pattern matches (so the memory reads exactly as the user phrased it), `None` otherwise — most messages produce no candidate at all, which is correct, not a gap: not every exchange contains a durable fact.
- **Retrieval** (`app/memory/retrieval.py`): `retrieve_relevant_memories(project_scope, query, top_k, token_budget, store, embedding_model) -> list[str]`, structurally identical to `app/rag/retrieval.py`'s `retrieve_relevant_chunks` (same cosine-ranking-then-token-budget-trim shape) — deliberately the same shape as the already-reviewed RAG retrieval function, not a new design.
- **Chat integration** (`app/api/chat.py`): when `Settings.ENABLE_PROJECT_MEMORY` and `request.lair_project_scope` are both set, relevant memories are retrieved and injected as a system message before compression (same position document retrieval already occupies), and — after a successful non-cached, non-cloud completion — the user's prompt is run through `extract_candidate_memory` and, if it matches, written via `store.remember()`. `lair_meta.memory_injected_count` reports how many memories were used; `0`/omitted when the feature is off or nothing was retrieved.
- **Token budget**: `min(Settings.MEMORY_TOKEN_BUDGET, context_window // 4)` when the routed model's context window is known — a quarter of context (not RAG's half) because memory is background continuity, not the primary content of the request the way an ingested document's excerpts are.

---

# Alternatives Considered

## SQLite + a real vector index

Cons

- Every other store in the codebase is JSON-backed (`KnowledgeBase`, `DecisionRepository`, `ResponseCache`, `DocumentStore`, `CloudBudgetLedger`); introducing SQLite here is a second persistence idiom with no scale-driven justification at "one user's project memory" size — see RFC-0002 for the full reasoning.

## Cross-scope similarity matching for dedup

Cons

- A high similarity score between memories from two different projects is very likely coincidental phrasing, not the same underlying fact — merging across scopes would leak one project's memory into another's, violating the RFC's explicit scoping guarantee.

## Storing raw conversation turns instead of extracted statements

Cons

- Injecting whole turns back into future requests re-introduces exactly the context bloat I-09 (context compression) exists to prevent; extracted, deduped statements are the smaller, higher-signal representation the plan's own design notes call for.

---

# Consequences

Benefits

- Same JSON-backed idiom as every other store — no new operational surface, no new dependency
- Reuses I-08's `EmbeddingModel` directly; adds zero new ML dependencies
- Dedup keeps a scope's memory set small and current rather than accumulating near-duplicate noise over time

Trade-offs

- Heuristic extraction is a real, documented gap — genuinely useful facts phrased outside the trigger patterns are missed; promoting to model-assisted extraction is named future work in RFC-0002, not built speculatively here
- JSON-backed storage means `remember()` rewrites the full scope's file on every write, same cost profile as every other store in this codebase — fine at expected scale, a real limit only if a single scope's memory count grows very large

---

# Decision Summary

Persistent project memory ships as a JSON-backed, embedding-deduped, per-scope store built entirely from infrastructure I-07/I-08 already established — no new dependency, no new persistence idiom, off by default, and fully inspectable/revocable via `lair memory`.
