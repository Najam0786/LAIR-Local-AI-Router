# ADR-0021 — Streaming-Aware Routing: Schema + Hardware Signal (Execution Deferred)

**Status:** Accepted

**Date:** 2026-07-25

---

# Context

`docs/INNOVATION_PLAN_2026.md` I-16 asks LAIR to treat "larger than RAM, but runnable slowly via SSD streaming" as an explicit, explained routing tier instead of a hard refusal, so a student with a fast SSD but 8GB RAM can still get an answer from a 30B-class model on the rare question that truly needs one.

The plan's own design notes are explicit about the real gap: "LM Studio doesn't expose streaming knobs, so this tier initially targets a llama.cpp-direct provider... natural companion to the Multi-Provider milestone (v0.5)." That provider does not exist in this codebase yet -- LM Studio is still the only registered provider (ADR-0002/ADR-0013), and it does not expose mmap/streaming tuning. This ADR therefore scopes I-16 to what's honestly buildable now: the hardware signal, the registry schema, and the routing-side allowance logic -- with the actual streaming execution path explicitly deferred, the same way ADR-0019 deferred scanned-PDF OCR and ADR-0017 deferred backend KV-quant control, rather than fabricating a capability nothing in this codebase can yet perform.

---

# Decision

- **A real, best-effort SSD read-speed benchmark** (`app/hardware/ssd_benchmark.py`), run once by `lair doctor` (like GPU detection, not on the routing hot path -- see `LocalHardwareProvider`'s own docstring on why per-request hardware re-detection is avoided). Writes and reads back a 64MB temp file; honestly documented as an optimistic proxy (may reflect OS page-cache speed, not guaranteed cold-disk I/O) rather than a lab-grade unbuffered benchmark.
- **`streaming_viability`**: a 0.0-1.0 score derived from that read speed (`0.3GB/s` → 0.0, `3.0GB/s+` → 1.0, linear between). `DoctorReport` carries both fields; `lair doctor --init` persists `streaming_viability` onto the saved `Portfolio` (`configs/active_portfolio.yaml`) -- the same already-established persistence path I-12 uses for `hardware_tier`, not a new store.
- **Registry schema change**: `ModelMetadata.streamable: bool = False` (`app/providers/model_metadata.py`). Always `False` from the real LM Studio provider today -- no provider in this codebase sets it `True` yet. `app.hardware.resource_resolver.detect_streamable(is_moe) -> bool` is a heuristic (`== is_moe`) matching the plan's own "MoE is the priority streamable class" reasoning (few active params/token means most of a partially-streamed model's weights are never touched for a given token; a dense model needing full-weight streaming would be far too slow to be worth surfacing this pass).
- **`filter_by_hardware()` gains a streaming allowance**, not a replacement for the hard fit check: a model that fails the normal RAM-fit test is still kept when (a) `Settings.ENABLE_STREAMING_ROUTING` is on, (b) this machine's `streaming_viability` clears `Settings.STREAMING_MIN_VIABILITY`, (c) the model is declared `streamable`, and (d) a heuristic latency-multiplier estimate (needed-vs-available memory ratio -- not a measured figure) is within `Settings.STREAMING_MAX_LATENCY_MULTIPLIER`. All four conditions, always -- mirrors RFC-0001's "gate, not a scored preference" reasoning for something this consequential (a pick that will be genuinely, noticeably slow).
- **`ModelScorer` labels, never boosts, a streaming pick**: a purely explanatory `streaming_pick` factor (score `0.0`) states the model exceeds available RAM and gives the estimated slowdown multiplier. No score bonus -- being admitted at all (only when the filter had no other choice) is the only encouragement it needs; a fitting candidate always wins on ordinary scoring grounds.
- **Off by default** (`Settings.ENABLE_STREAMING_ROUTING = False`). Even though nothing in this codebase can currently execute a streaming pick (no llama.cpp-direct provider exists to actually load a model this way), leaving the schema/allowance dormant-but-real means a future Multi-Provider-milestone provider can flip it on without another schema change.

---

# Alternatives Considered

## Build a llama.cpp-direct provider now, to fully satisfy I-16's execution acceptance criterion

Cons

- A whole new provider (process management, a different completion API shape, mmap/`--no-mmap`/`--mlock` tuning) is squarely the Multi-Provider milestone's (v0.5) job, not a one-pass addition to an otherwise-routing-focused item; building it here would be exactly the kind of premature, undirected scope the project's own engineering discipline warns against.

## Infer `streamable` for every model unconditionally (not gated on `is_moe`)

Cons

- The plan itself singles out MoE as the class actually worth streaming (few active params/token); marking dense models streamable too would surface "slow but possible" picks that in practice would be far past any reasonable latency bar -- not fabricated, just not useful yet.

## Skip the hardware/schema work entirely until the Multi-Provider milestone ships

Cons

- The SSD benchmark, `streaming_viability`, and the registry schema are independently useful and testable now, and de-risk the eventual provider work (the routing-side gate is already built and tested against real hardware signal) -- shipping the honestly-scoped half is better than shipping nothing.

---

# Consequences

Benefits

- Real, working hardware signal (`lair doctor`) and a fully tested routing-side allowance/labeling path, ready for a future streaming-capable provider to plug into without another schema change
- No fabricated capability: nothing in this codebase claims to execute a streaming pick today, and the feature is off by default

Trade-offs

- The plan's own acceptance criterion "one oversized MoE model demonstrably answers... via streaming, with recorded tok/s" is **not met this pass** -- it requires a working llama.cpp-direct provider that doesn't exist yet; tracked as follow-up work tied to the Multi-Provider milestone, not silently dropped
- The SSD benchmark's honest caveat (page-cache-influenced, not guaranteed cold I/O) means `streaming_viability` is a real-but-imperfect signal, not a lab-grade measurement
- The latency-multiplier estimate is a memory-ratio proxy, not a measured slowdown -- consistent with, but as approximate as, the KV-cache memory formula's own documented approximation (ADR-0017)

---

# Decision Summary

I-16 ships its hardware-signal and registry-schema half in full -- a real SSD benchmark, a derived viability score persisted the same way I-12 persists hardware tier, a `streamable` schema field with an honest MoE-based heuristic, and a tested routing-side allowance/labeling path -- while honestly deferring the actual streaming execution path to the Multi-Provider milestone, where a real llama.cpp-direct provider can plug into infrastructure that already exists and is already tested.
