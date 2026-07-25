# ADR-0014 — Execution Runtime Boundary

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

Every milestone through Provider Metadata Grounding (ADR-0013) strengthened LAIR's *decision* about which model should handle a prompt. Nothing acted on that decision — `/route` returned an `ExecutionPlan` naming the chosen model, and the caller had to go use that model manually, through LM Studio or another client. That gap was the actual bottleneck: not routing quality, but usability. The concrete goal is an OpenAI-compatible surface so tools like Continue, Cline, Cursor, and Open WebUI can point their base URL at LAIR instead of LM Studio directly, and get automatic routing for free.

Scoping this milestone (four rounds of external-reviewer feedback, engaged with critically rather than accepted wholesale) surfaced a real bug in the existing code, not just a future concern: `RoutingEngine.route()` called `decision_repository.record(decision)` directly inside the decide step — a side effect inside what should be a pure computation. Fixing that boundary is inseparable from adding execution, since execution is exactly the thing that needed a place to live once decide and persist were split apart.

Three abstractions were proposed during scoping and rejected, each for the same reason — no real second consumer existed to justify them:

- **A persisted Session Manager** (server-side conversation history, token budgets, context trimming, session IDs). Every target client — Continue, Cline, Cursor, Open WebUI — already resends the complete message history on every request, exactly like the OpenAI API itself. LAIR staying stateless matches how these clients actually behave; building session persistence now would be speculative.
- **A separate `ProviderAdapter` layer** between the Runtime and `BaseProvider`. `BaseProvider` already is that adapter — `LMStudioProvider` already translates HTTP/JSON into `AIModel`/`CompletionResult` — and there is still only one provider implementation. A second named layer on top of an interface with one implementation adds nothing.
- **A formal Application Service class.** The two callers that need to coordinate "decide, then persist" (`/route`, decide-only) and "decide, execute, then persist" (`/v1/chat/completions`) each do so in a handful of lines. A shared abstraction is worth extracting only once a third real caller needs the same sequence.

---

# Decision

**The Decision Engine computes; it has no side effects.** `RoutingEngine.route()` no longer accepts or calls a `DecisionRepository` — it takes a `Task` and a list of `AIModel`s and returns an `ExecutionPlan`. It may analyze, filter, score, and rank. It may not execute, persist, benchmark, or call a provider.

**The Execution Runtime executes; it has no persistence.** `app/execution/runtime.py` exposes one function, `execute(model, messages, max_tokens)`, that looks up the provider via `provider_registry.get()`, invokes `.complete()`, and translates the result into a `CompletionResult` plus an `ExecutionOutcome`. It never raises — a failed provider call becomes `ExecutionOutcome(success=False, error=...)`, not an exception — and it never touches FastAPI, `HTTPException`, or `DecisionRepository`.

**The API handlers coordinate.** `app/api/routing.py` and `app/api/chat.py` each call `routing_engine.route()`, then do whatever their endpoint needs — the `/route` handler persists the decision immediately; the `/v1/chat/completions` handler additionally calls `execute()`, attaches the resulting `ExecutionOutcome` onto the `DecisionRecord` via `model_copy()`, and persists that. No new orchestration class exists to do this on their behalf.

**`Conversation` is a request-scoped value object, not a session.** `app/execution/conversation.py` wraps the `messages` array from an OpenAI-shaped request and exposes `latest_user_message()` — used to build the `Task` the Decision Engine reasons about. The full message list (system prompt, prior turns) is passed to `execute()` for generation, so conversational context is preserved even though routing only reasons about the latest turn's intent. Nothing is persisted between requests.

**`BaseProvider.complete()` takes a full message list, not a flat string.** Flattening multi-turn history into one string before this milestone even shipped would have quietly defeated the point of using LAIR as a coding-assistant backend — no memory of earlier turns. `complete(model_id, messages: list[dict], max_tokens)` now passes the real conversation through to the provider unmodified.

**`ExecutionOutcome` carries only what `DecisionRecord` doesn't already have.** `success`, `latency_ms`, `completion_tokens`, `prompt_tokens`, `finish_reason`, `error` — no `model`/`provider` fields, since those already live on `DecisionRecord.selected_model` and duplicating them risks the two drifting out of sync.

**Non-streaming only.** Streaming changes the HTTP lifecycle, cancellation, and buffering — a materially different, larger problem than translating a synchronous request/response. A `stream: true` request gets an explicit `400`, not a silent downgrade or a hang.

---

# Implementation Notes

**Request sequence:**

```
Continue
  -> POST /v1/chat/completions
  -> Conversation (parses messages[])
  -> Task (conversation.latest_user_message())
  -> routing_engine.route()            [pure: analyze, filter, score, select]
  -> ExecutionPlan
  -> execution.runtime.execute()       [invokes provider, no persistence]
  -> ExecutionOutcome
  -> DecisionRecord.model_copy(execution_outcome=...)
  -> default_decision_repository.record()
  -> ChatCompletionResponse            [OpenAI-shaped]
```

**Request/response mapping:** the client's `model` field is accepted and ignored (LAIR's routing decides); `messages[]` maps to `Conversation`; the response's `model` field reports the model LAIR *actually* selected, which may differ from what the client sent — that's the entire point. `max_tokens` defaults to `1024` in the chat schema, not `complete()`'s own default of `64` (that default was tuned for quick benchmark pings and would silently truncate every real answer).

**Non-goals for this milestone (explicit, not oversights):** streaming, persisted sessions/token budgets/context trimming, retries, fallback providers, multi-provider support, adaptive per-turn model-affinity switching, and Learning Engine consumption of the new `execution_outcome` data. Each is a legitimate future milestone; none is a prerequisite for a working OpenAI-compatible endpoint.

---

# Alternatives Considered

## Persisted Session Manager

Cons

- No client this milestone targets (Continue, Cline, Cursor, Open WebUI) needs it — all of them already resend full history per request, matching the stateless OpenAI API model
- Speculative architecture: token budgets, context trimming, and session IDs solve a problem LAIR doesn't currently have

## Separate ProviderAdapter Layer

Cons

- `BaseProvider` already fulfills this role; there is still exactly one provider implementation
- A second adapter layer on top of a single-implementation interface adds indirection with no behavioral benefit

## Formal Application Service Class

Cons

- The two real call sites' orchestration sequences are each a handful of lines and genuinely differ in shape (persist-immediately vs. execute-then-persist)
- Extracting a shared abstraction before a third caller needs it repeats the same premature-abstraction mistake rejected for the other two alternatives

## Flatten Conversation History into a Single Prompt String

Cons

- Keeps `BaseProvider.complete()`'s signature unchanged, but discards system prompts and prior turns into one undifferentiated block of text
- Directly undermines the milestone's purpose — a coding assistant that forgets everything except the current message is not meaningfully more useful than the existing `/route`-and-copy-manually workflow

---

# Consequences

Benefits

- LAIR is usable end-to-end for the first time: a client can send a prompt and receive a real answer, not just a recommendation
- Any OpenAI-compatible client works by changing only its base URL — no custom integration per tool
- The Decision Engine's purity is now enforced by the code, not just documented intent — testable and replayable in isolation from persistence and execution
- `DecisionRecord.execution_outcome` starts collecting real-traffic latency/success/token data, the raw material a future Learning Engine needs and that pure benchmark data alone doesn't provide

Trade-offs

- No streaming yet — real clients will see the full response appear at once rather than progressively, a materially different (worse) experience for long answers until a follow-up milestone adds it
- No persisted conversation memory beyond what the client itself resends — acceptable today because every targeted client already behaves this way, but would need revisiting if a genuinely stateless-incompatible client shows up
- `BaseProvider.complete()`'s signature change is a breaking internal change (touches `LMStudioProvider`, `BenchmarkRunner`, and every test double) — contained to a handful of files, but real churn, taken on deliberately rather than preserving a string-only signature that would have quietly broken multi-turn fidelity

---

# Decision Summary

LAIR stops being a service that only recommends and starts being one that answers — by keeping the Decision Engine pure, giving execution a thin dedicated home, and refusing to build session state, a provider adapter, or an orchestration class that nothing yet needs.

---

# Update (M6.1) — Streaming Added

The "non-streaming only" decision above held until real dogfooding produced concrete, reproduced evidence it couldn't: Cline's "OpenAI Compatible" provider always sends `stream: true` with no setting to disable it anywhere in its UI, so it could not complete a single request against LAIR as originally shipped (`docs/DOGFOODING.md`, DF-002/DF-003). This wasn't speculative scope-creep — it was confirmed by direct reproduction before any code changed.

Streaming was added following the same boundaries this ADR already established: `BaseProvider.stream_complete()` is a concrete default method (falls back to `complete()`, yielding one simulated chunk), not a new abstract method — there is still exactly one real streaming implementation (`LMStudioProvider`), so forcing every provider (including the `FakeProvider` test double) to hand-roll chunking had no real second consumer. `execution.runtime.stream_execute()` mirrors `execute()`'s "never raises" contract as a terminal `StreamEvent(error=...)` instead of a raised exception, since HTTP headers are already committed once a stream starts and status codes can no longer change. Accumulation and persistence of `DecisionRecord.execution_outcome` stayed in the API handler, not the runtime, per this ADR's existing division of responsibility — no new orchestration class was introduced.

The original reasoning above (streaming is a materially larger problem than a flag, deferred deliberately) remains accurate as historical context for why it didn't ship in M6 — this update documents that the deferral ended once real evidence, not architectural taste, said it needed to.
