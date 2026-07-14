# Dogfooding Log

Real observations from using LAIR for daily work through Continue (and any
other OpenAI-compatible client), collected before scoping Multi-Provider,
Learning Engine, or further routing changes. Evidence from here drives what
gets built next — not the reverse.

Each entry: what was observed, when, and what it might imply. Not every
entry needs fixing immediately, or ever — the point is to notice, not to
react.

Capture the observation before interpreting it. Record what happened, not
the fix — jumping straight to "model switched twice → need conversation
pinning" optimizes for a single anecdote. One observation is just an
observation. Two similar ones suggest a possible pattern worth watching.
Three or more independent ones justify actually discussing a change.

Format stays loose (date, observation, implication, status) rather than a
fixed schema — with one entry there's no evidence yet for what fields
actually matter across real observations. Let structure emerge from the
log itself if it turns out to be needed, the same way everything else in
this project waits for a real second case before formalizing.

---

## DF-001 — Reasoning models can exhaust the token budget before answering

**Observed:** 2026-07-14, smoke-testing `/v1/chat/completions` against
`deepseek-r1-distill-qwen-32b` with `max_tokens: 30`. Response came back
with empty visible content and `finish_reason: "length"` — the model spent
its entire budget on hidden `<think>` reasoning tokens before it could
write anything visible.

**Implication:** low `max_tokens` values can produce apparently-empty
responses despite the request succeeding end-to-end — not a bug, but a
real characteristic of reasoning-style models specifically. Possible future
angles, none acted on yet:
- Per-model-family default generation parameters (reasoning vs. non-reasoning)
- `RoutingPolicy` eventually accounting for reasoning overhead
- A future Learning Engine adapting generation parameters per model, once
  there's enough real traffic to learn from

**Status:** open, informational — Continue's config already defaults to
`maxTokens: 1024`, which should give enough headroom for normal use; watch
for it recurring in real conversations, not just this synthetic test.

---

## DF-002 — Experiment: is agentic tool-use blocked by LAIR or by the model?

**Objective:** not "does agent mode work" — identify *where* it breaks if
it does. `ChatCompletionRequest` doesn't accept a `tools` field today
(see ADR-0015), so this experiment should show one of two distinct
failures, and they imply different things:

- Tools are never invoked / silently ignored → LAIR's missing `tools`
  passthrough is the bottleneck, and closing that gap becomes a real,
  evidence-backed next step.
- Tools are sent through fine but the model calls them unreliably or
  incorrectly → the bottleneck is local model tool-calling capability,
  which no amount of LAIR work fixes.

**Method:** point Cline (already installed) at LAIR
(`http://localhost:8001/v1`) and give it one small, real, well-scoped task
that requires reading or editing a file. Not a survey of every
OpenAI-compatible client (Continue, Open WebUI, Aider, Goose, Roo Code,
etc.) — one agent-capable client is enough to answer *this* question;
broader ecosystem testing is a separate thing to do later, only if there's
a real reason to.

**Result:** *pending — fill in after trying it.*

**Conclusion:** *pending.*
