# CLAUDE.md — LAIR Project Context

This file gives Claude Code standing context for every session. Read it fully before making changes. Do not re-ask the user for information that is already here.

## What LAIR Is

LAIR (Local AI Intelligence Router) is a local-first, provider-agnostic router that automatically selects the best local LLM for each task. Users describe problems; LAIR picks the model. Core pillars: **capability-aware, benchmark-driven, explainable, local-first, low-cost**.

Mission additions (2026): make AI affordable (avoid cloud token costs) and accessible (run well on ordinary 8–16GB laptops, not just 64GB workstations).

## Current State

- Version: v0.1.0-alpha, moving toward 0.2 (Capability Engine)
- Working: FastAPI server (`main.py`), OpenAI-compatible `/v1/chat/completions`, LM Studio provider with automatic server/model lifecycle management, Benchmark Engine + KnowledgeBase (Milestone 2), soft-scoring routing filters
- Backend: LM Studio only (Ollama, vLLM planned for v0.5)
- Model portfolio: Qwen3.6 35B A3B (coding), Gemma 4 26B A4B (docs), DeepSeek-R1 Distill Qwen 32B (reasoning), Qwen2.5-VL 7B (vision), Qwen3 8B (fast assistant)

## Repository Layout

```
app/           — application code (routing, providers, models, execution)
architecture/  — ARCH-xx numbered architecture documents
benchmarks/    — benchmark definitions and results
configs/       — configuration files
docs/          — product vision, routing engine, registry, ADRs, RFCs, research,
                 innovation_backlog.md, INNOVATION_PLAN_2026.md (the active plan)
prompts/       — prompt templates
scripts/       — utility scripts
tests/         — pytest suite (run with `pytest` from repo root, see pytest.ini)
main.py        — FastAPI entry point (uvicorn main:app --reload, port 8000)
```

## Engineering Workflow (MANDATORY for significant features)

Innovation Backlog → Research → Prototype → RFC → ADR → Implementation → Testing → Benchmarking → Release

- Significant features get an RFC in `docs/` before code; accepted decisions get an ADR.
- Architecture precedes implementation. Evidence precedes optimization.
- Small fixes and refactors may skip RFC/ADR but still need tests.

## Conventions

- **Commits:** Conventional Commits — `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`. Imperative mood, concise subject. Example from history: `feat: auto-manage LM Studio's server/model lifecycle from LAIR`
- **Python:** 3.13+, Pydantic models for all data structures, HTTPX for outbound calls, type hints everywhere.
- **Tests:** every feature ships with pytest tests in `tests/`. Run the suite before committing.
- **Docs:** update `CHANGELOG.md` on every release-worthy change; update `ROADMAP.md` when milestone status changes; keep `README.md` model portfolio and roadmap tables in sync.
- **Routing principle:** the routing engine never performs inference; it only decides who does. Registry holds metadata only. Each subsystem has one responsibility.

## Active Plan

The current strategic direction lives in **`docs/INNOVATION_PLAN_2026.md`**. When the user asks to "implement the next feature" or "continue the plan," read that file and pick up from its Implementation Sequence section. Each entry there has acceptance criteria — meet them before marking anything done.

## Key Design Constraints (do not violate)

1. Local-first: never send user prompts to any cloud API unless the hybrid-routing feature is explicitly enabled AND within the user's budget cap.
2. Explainability: every routing decision must produce a machine-readable explanation (selected model, scores per factor, provenance tag per factor: MEASURED / DECLARED / HEURISTIC).
3. Graceful degradation: on low RAM/VRAM, prefer a smaller model or quant over failing. Never crash with OOM if a fallback exists.
4. OpenAI compatibility: `/v1/chat/completions` must remain drop-in compatible with Continue, Cline, Cursor, and similar clients.
5. LM Studio integration uses its native features where possible: JIT loading, `ttl` in request payloads, Auto-Evict, and `draft_model` for speculative decoding — do not reimplement what LM Studio provides.

## Token-Efficiency Rules for Claude Code Sessions

- Do not re-read the full docs/ tree each session; this file plus the specific doc you're changing is usually enough.
- Prefer `docs/INNOVATION_PLAN_2026.md` §Implementation Sequence over asking the user what to build.
- When context is needed on routing design, read `docs/routing_engine.md`; on architecture, `docs/architecture.md`; on backlog format, `docs/innovation_backlog.md`.
