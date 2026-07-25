# ADR-0019 — RAG-Lite Document Pipeline

**Status:** Accepted

**Date:** 2026-07-25

---

# Context

`docs/INNOVATION_PLAN_2026.md` I-08 asks for local document ingestion + retrieval so a small local model can answer questions over documents far larger than its context window — chunk and embed once, retrieve only the relevant slices per question. Nothing in LAIR touched embeddings before this; the choice of embedding library is a real, dependency-weight-relevant decision worth recording.

---

# Decision

- **`fastembed` (ONNX Runtime), not `sentence-transformers` (PyTorch).** `sentence-transformers` pulls in `torch` — hundreds of MB, meaningfully at odds with a project whose own mission is running well on ordinary 8–16GB laptops (`docs/INNOVATION_PLAN_2026.md`'s Mission B). `fastembed` gets real local embeddings (`BAAI/bge-small-en-v1.5`, a genuine MiniLM-class model, `Settings.RAG_EMBEDDING_MODEL`) without it.
- **The embedding model is fetched from Hugging Face Hub once, on first real use, and cached on disk after that** — the same one-time-acquisition pattern as an LM Studio model download, not a per-request network dependency. `EmbeddingModel` (`app/rag/embeddings.py`) is lazy: importing it, or constructing one, never triggers a download by itself.
- **Chunking is word-based** (`app/rag/chunking.py`), converting a token budget to a word count via the same ~4-chars/token rule of thumb I-09's `estimate_tokens` already established — one calibration constant for "approximate token count" across the codebase, not two differently-tuned ones.
- **PDF extraction is text-only** (`pypdf`). Scanned-page OCR via a local vision model, named in I-08's design notes, is explicitly deferred: rendering a PDF page to an image needs a rasterization dependency (e.g. poppler, a system binary, not pip-installable) this pass doesn't introduce, and I-08's own acceptance criteria targets text PDFs specifically.
- **Storage is "lite" per the plan's own words: no external vector DB.** `DocumentStore` (`app/rag/store.py`) is JSON-backed, matching every other store in this codebase; retrieval (`app/rag/retrieval.py`) loads a document's chunks into memory and computes cosine similarity directly — appropriate at the scale a single local user's document set reaches, not built for a large multi-tenant corpus.
- **Retrieval is explicit, not auto-detected.** `ChatCompletionRequest.lair_document_id` (mirroring `lair_no_cache`'s established pattern of small, explicit, opt-in LAIR-specific fields) tells LAIR which ingested document a conversation is about; relevant chunks are retrieved against the latest user message and injected as a system message before the request reaches the provider. Auto-detecting "does this conversation reference an ingested document" from free text was considered and rejected as unnecessary complexity — the client already knows which document it's asking about.
- **Retrieval respects the actually-selected model's context window**, not a fixed constant: `Settings.RAG_RETRIEVAL_TOKEN_BUDGET` is capped at half the selected model's `context_window` when known, satisfying I-08's "retrieval context fits the target model's context budget" against whatever model I-03's routing actually picked, not a guess made in advance.

---

# Alternatives Considered

## `sentence-transformers` / PyTorch-based embeddings

Cons

- Torch's install footprint directly contradicts the project's own accessibility mission for a laptop-class tool

## Auto-Detect Document References from Conversation Text

Cons

- Real complexity (another classification problem) to replace something the client already knows and can state explicitly; deferred as unnecessary speculative work, not built ahead of real demand

## A Real Vector Database (e.g. an embedded one like sqlite-vec or a standalone service)

Cons

- The plan's own design notes say "keep it lite: no external vector DB dependency by default" — a JSON store plus in-memory cosine similarity is sufficient at the scale a single local user's ingested documents reach; revisit only if real usage shows otherwise

---

# Consequences

Benefits

- Real, working semantic retrieval (verified end-to-end against a 105-page synthetic PDF with three distinct sections, each correctly retrieved for its own targeted question) without a heavy new runtime dependency
- Retrieval budget is grounded in the actual routed model's real context window, not a fixed assumption

Trade-offs

- Scanned/image-only PDF pages currently yield no extractable text — a real gap for scanned documents specifically, not silently mishandled (an empty string, not a crash or a guess), but genuinely deferred work
- In-memory cosine similarity over a document's full chunk set doesn't scale to a very large document corpus -- fine at today's expected usage, a real limit if that changes
- The embedding model's first-use download is a real, if one-time, network dependency -- offline-from-first-boot usage needs it pre-cached

---

# Decision Summary

RAG-lite ships with real local semantic retrieval via a torch-free embedding stack consistent with LAIR's own accessibility mission, explicit (not guessed) document scoping per request, and a retrieval budget grounded in the actually-selected model's real context window -- with scanned-PDF OCR and large-corpus scaling both honestly deferred rather than fabricated.
