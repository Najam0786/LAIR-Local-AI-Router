# ADR-0015 — Runtime vs. Agent Boundary

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

After Milestone 6 shipped a real OpenAI-compatible endpoint, the same question surfaced twice, independently, in real conversation: can LAIR become something like Claude Code — read the project, edit files, run commands, push to git — once a client is pointed at it? That question kept recurring because the answer wasn't written down anywhere, only implied by how Milestone 6 was scoped.

The honest answer is structural, not a LAIR-specific limitation: an agentic coding assistant is two things bolted together — an **agent loop** (plan the next step, call a tool, feed the result back, repeat) and a **model** that reasons about what to do next. The agent loop — reading files, editing them, running a shell, calling git, indexing a project, holding conversation/session state — has never been something LAIR does or was ever scoped to do. `ExecutionPlan`/`ExecutionOutcome` execute *one* model call and return; they don't plan, don't call tools, don't touch the filesystem. Continue, Cline, Cursor, and Claude Code itself all own that loop themselves, sitting *above* whatever serves the model.

This is the same boundary ADR-0014 draws between the Decision Engine and the Execution Runtime, one level up: just as the Decision Engine must not reach into execution or persistence, LAIR as a whole must not reach into the agent's job. Writing it down now, rather than re-answering it from scratch each time it comes up, is justified the same way the Engineering Handbook's Evolution Principle was — this is documenting a boundary that's already been independently tested by real questions, not speculating about one.

---

# Decision

**LAIR is an AI Decision & Execution Runtime.** It decides which model should handle a request, executes that request against the chosen provider, and returns the result through a standard (OpenAI-compatible) API. That is the entire contract.

**LAIR does not become an IDE, an autonomous coding agent, or a tool runner.** It will never own: file system access, git/GitHub operations, a terminal, project indexing, MCP tool execution, conversation/session persistence, or planning. Those are the agent's job — Continue, Cline, Cursor, Claude Code, or whatever client sits on top — never LAIR's.

**What LAIR exposes today, under this contract:**
- `POST /v1/chat/completions`, `GET /v1/models` — OpenAI-compatible execution (ADR-0014)
- `GET /models` — LAIR's richer model/capability listing
- `GET /benchmarks` — measured throughput per model
- `POST /route` — decision-only, for callers that want the recommendation without execution

**What's explicitly *not* decided yet, deferred until real demand exists, not built speculatively:** surfacing routing reasoning (`confidence`/`reasons`) through the chat-completion response itself (today it's only visible via `/route` or `logs/decisions.json`); exposing benchmark or hardware-constraint data as a first-class capability for external agents to query before choosing to call LAIR. Both are plausible, neither has a real consumer asking for them yet.

**Tool-calling passthrough (`tools`/`tool_calls` in the OpenAI schema) is not built.** `ChatCompletionRequest` doesn't accept a `tools` field today — Pydantic silently drops unrecognized fields, so a client sending them gets no error and no tool-calling behavior. Whether this is worth building is an open question, gated on the DF-002 experiment (below) actually showing LAIR's missing passthrough — rather than local model tool-calling reliability — is the real bottleneck.

---

# Alternatives Considered

## LAIR Grows Its Own Agent Capabilities (File Editing, Git, Tool Loop)

Cons

- Duplicates what Continue/Cline/Cursor/Claude Code already do well, and duplicates it *worse* — LAIR would need to reinvent project indexing, diff application, and a planning loop from scratch
- Turns LAIR into a single opinionated coding-assistant workflow instead of a backend any OpenAI-compatible client can use — the opposite of what made Milestone 6 valuable
- Blurs the exact boundary ADR-0014 just finished drawing one layer down (Decision Engine vs. Execution Runtime); repeating the mistake one layer up

## Leave the Boundary Implicit, Re-decide It Each Time It Comes Up

Cons

- Already happened twice in one project; the question will keep recurring for every future contributor or client integration without a canonical answer to point to

---

# Consequences

Benefits

- LAIR stays composable — any OpenAI-compatible client (present or future) can sit on top without LAIR needing to know or care which one
- Scope stays bounded: routing, execution, knowledge, learning — not an ever-expanding surface chasing feature parity with coding assistants
- Future contributors and integrations have a canonical answer instead of re-deriving one

Trade-offs

- Users wanting a fully local "Claude Code" experience need a capable agent client (Continue/Cline/Cursor) *and* a local model good enough at tool-calling *and*, potentially, LAIR's tool-passthrough gap closed — three separate dependencies, none of which LAIR alone can guarantee
- LAIR's value to that workflow is real but partial: it makes the model-selection step better, it doesn't make the agent loop or the model's raw capability better

---

# Decision Summary

LAIR picks and runs the model; it never becomes the thing driving the coding session. That boundary is what lets it plug into an entire ecosystem of agent clients instead of competing with one of them.
