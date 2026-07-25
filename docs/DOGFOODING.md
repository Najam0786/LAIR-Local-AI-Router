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

**Result:** blocked before reaching the actual tool-calling question twice
in a row — first by the streaming requirement (fixed, see M6.1), then by
a context-window/model-configuration issue surfaced by DF-004 below,
unrelated to LAIR.

**Conclusion:** still open whether LAIR's missing `tools` passthrough or
model tool-calling capability is the eventual bottleneck — but DF-004
shows the more immediate blocker (context window fit for Cline's large
prompts) sits below LAIR entirely, in model/provider configuration.

---

## DF-004 — Direct LM Studio test confirms the blocker isn't LAIR (and going through LAIR likely avoids it)

**Observed:** 2026-07-14, testing Cline → LM Studio directly
(`http://localhost:1234/v1`, bypassing LAIR entirely) to isolate whether
a failure was LAIR-specific. It failed too — with LM Studio's own native
error ("check developer logs... load the model with a larger context
length... enable Compact Prompt"), not a connection or schema error.
Cline had requested `google/gemma-4-26b-a4b-qat` by name — a model that
was never actually loaded in LM Studio (only `deepseek-r1-distill-qwen-32b`
is loaded) and, when loaded, would likely have a configured context window
too small for Cline's large tool-heavy system prompt.

**Implication:** the failure is model/context configuration, not LAIR —
confirmed by reproducing it with LAIR completely out of the picture.
Notably, going through LAIR instead of direct likely sidesteps this exact
failure mode: LAIR's loaded-state filter means it would only ever have
routed to `deepseek-r1-distill-qwen-32b` (the one loaded model, with a
131,072-token context window) regardless of which model Cline named,
whereas the direct path let Cline pick an unloaded, likely small-context
model by name with nothing to catch it.

**Status:** resolved as "not a LAIR bug." Next step is retrying via LAIR
(not direct) to see how far that gets, now that the direct path has ruled
out LAIR as the cause.

---

## DF-005 — Deprioritizing Cline for dogfooding; Continue is the more reliable client so far

**Observed:** 2026-07-14. Across DF-002 through DF-004, Cline required
fixing three separate compatibility gaps to even get a request through
(base-URL path-joining convention, list-of-parts message content, hard
streaming requirement) and still hit the model-context-window issue
(DF-004) before any real tool-calling test was reached. Meanwhile,
Continue worked cleanly from the first test (the earlier multi-turn
context-recall check) and, per direct user report, consumes real tokens
in LM Studio successfully switching between models manually.

**Implication:** this isn't necessarily evidence against LAIR — DF-004
showed Cline's friction was mostly client-side (config conventions,
prompt size) rather than a LAIR defect. But for the purpose of *using*
LAIR productively during this dogfooding phase, Continue is the more
practical client to standardize on for now.

**Status:** open — decided to focus remaining dogfooding on Continue
through the "LAIR (Auto-routed)" entry specifically (not the direct
"Autodetect" entries), rather than continuing to debug Cline's
config. Revisit Cline later if there's a specific reason to (e.g. its
agent-mode capabilities become the priority again).

---

## DF-002 (conclusion) — First confirmed real end-to-end round trip via Continue

**Observed:** 2026-07-14, selecting "LAIR (Auto-routed)" in Continue's
Chat dropdown and asking a real question ("Could you please review my
project"). Confirmed via LAIR's server log (`POST /v1/chat/completions
-> 200 OK`) and the persisted `DecisionRecord` in `logs/decisions.json`,
whose `execution_outcome` (397 prompt tokens, 452 completion tokens)
matches exactly what Continue displayed. Full path verified:
Continue -> LAIR (routing decision) -> LM Studio (`google/gemma-4-26b-a4b-qat`,
auto-selected) -> real answer -> back through LAIR -> Continue.

**Implication:** this is the first real, user-facing confirmation that
the entire Milestone 6 + 6.1 stack works end-to-end with a real client,
not just curl/pytest. Latency was ~113 seconds for this response --
expected for a 26B model reasoning on local hardware, not a defect, but
worth keeping in mind for how "snappy" daily use will feel.

**Conclusion:** the original DF-002 question (is the bottleneck LAIR or
the model) is answered for Continue: neither was a bottleneck here, it
just worked. The tool-calling-specific question remains open for
whichever client picks that up next.

---

## DF-006 — Confirmed: LM Studio's own JIT loading + Auto-Evict can fully automate model switching; LAIR's hard loaded-filter is the only thing stopping it

**Observed:** 2026-07-14/15, investigating "we have to manually activate
each model" as a real, repeatedly-felt friction point all session.
Root-caused through direct experimentation against LM Studio's real API
and settings (not assumption):

1. LM Studio has genuine JIT loading (auto-loads an unloaded model on
   first API request) and Auto-Evict (unloads the previously *JIT-loaded*
   model when a new one is JIT-loaded) — both enabled by default.
2. First attempt at a live model swap (gemma -> deepseek) failed with
   "insufficient system resources," even though Auto-Evict should have
   freed enough RAM. Root cause: LM Studio's guardrail calculates
   available memory *before* eviction, not after — it doesn't trust the
   pending eviction, so it blocks upfront regardless of guardrail level
   (confirmed: "Relaxed" alone did not fix it).
3. `Default Context Length: Model maximum` was a separate, serious problem
   discovered along the way: it reserves KV cache for a model's *entire*
   max context (e.g. 262,144 tokens for gemma), ballooning the memory
   estimate to 33+ GB for a single model on a 32GB machine. Fixed by
   setting a bounded custom context length (32768) instead.
4. The actual fix for the swap: `Bypass Memory Load Warnings: No
   restriction` (not "Requires holding Alt/Option," which is unreachable
   for any API-driven request -- there's no human to hold a key). Combined
   with a bounded context length, this let a real swap succeed.
5. **Critical nuance:** Auto-Evict only evicts models that were *themselves*
   JIT-loaded. A model loaded manually via `lms load` (CLI) or the LM
   Studio UI is not eligible for automatic eviction and will happily sit
   alongside a second JIT-loaded model, exceeding system RAM (confirmed
   live: both ended up loaded simultaneously, ~35GB total on a 32GB
   machine, and the test request's connection dropped under the strain).
   Retesting with *both* models loaded via real API requests (matching
   how LAIR actually operates) confirmed clean, correct eviction: only
   the newly-requested model remained loaded afterward.

**Implication:** the entire "activate models automatically" problem is
already solved by LM Studio itself, given the right settings (bounded
context length, guardrails loosened enough, bypass set to "No
restriction"). LAIR does not need to build any model-loading automation.
The only remaining blocker is code, not infrastructure:
`RoutingEngine.route()`'s hard filter (`if model.loaded`) excludes any
unloaded model as a candidate before ever sending it a request — meaning
JIT loading never gets a chance to trigger through LAIR today. That
filter was correctly justified in ADR-0013 by real evidence at the time
(a request to an unloaded model returned a bare 400 with nowhere graceful
to go); it's no longer the same trade-off now that JIT loading is proven
to work AND Milestone 6 added `ExecutionOutcome`/graceful failure
handling downstream, which didn't exist when that filter was written.

**Status:** resolved at the infrastructure level. Next step: scope
loosening `RoutingEngine`'s loaded-model filter in LAIR itself (revisits
ADR-0013), now that the LM Studio side is fully validated with real,
repeated evidence rather than assumption.

---

## DF-007 — Loaded-model filter loosened and shipped; live-verified, plus a second real bug found and fixed the same night

**Observed:** 2026-07-15. Implemented the fix DF-006 called for:
`RoutingEngine.route()` no longer excludes unloaded models; `ModelScorer`
adds a soft `loaded_bonus_score` instead; `filter_by_hardware()` accounts
for RAM reclaimable from evicting currently-loaded models. Live-verified:

1. With **no model loaded**, a request through LAIR now succeeds (`200`,
   not `404`) and correctly triggers a real JIT load.
2. With a model loaded and a request that should prefer a different,
   unloaded model, the hardware filter correctly *rejected* the swap when
   real free RAM was genuinely too low (2.44 GB at that moment) --
   confirming the safety check still works, not a regression.
3. A **second, unrelated real bug** surfaced immediately after, live,
   through Continue's Agent mode: a richer real message ("please debug
   this python function and also translate this text and analyze this
   image") returned `404` even with plenty of RAM free and models
   available. Root cause: `CapabilityEngine.find_matching_profiles()`
   requires a model to satisfy **every** keyword-detected requirement
   simultaneously (AND logic) -- a longer, multi-topic message can trigger
   several different capability requirements that no single small local
   model satisfies all of at once, correctly-but-uselessly excluding every
   model. Fixed the same night: `RoutingEngine.route()` no longer uses
   `find_matching_profiles()` as a hard filter either -- capability
   matching is now scored only (`ModelScorer` already did this correctly
   per-requirement, no AND-logic problem there). `CapabilityEngine`
   itself is untouched, including its own dedicated AND-matching tests --
   only how `RoutingEngine` uses it changed.

**Implication:** the same "hard filter -> soft scoring preference"
pattern, applied twice in one session to two different filters, both
times triggered by a real message that a synthetic test prompt would
never have produced. Neither bug was visible until real, varied usage
(via Continue) exercised the system the way an actual user does.

**Status:** both fixes shipped, tested (75 tests passing), and
live-verified with the exact prompts that originally failed.
