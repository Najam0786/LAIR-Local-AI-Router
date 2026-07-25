# ADR-0012 — Hardware-Aware Filtering

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

LAIR had no awareness of hardware at all. Nothing stopped it from recommending a model that couldn't possibly fit in available memory.

Hardware constraints are a fundamentally different kind of reasoning than capability matching. Capability matching is a soft, scored preference — a model can be a better or worse fit for a task. Hardware fit is a hard, binary fact — a model either fits in available memory or it doesn't. It belongs in candidate filtering (a CSP-style hard constraint), not in scoring.

Scoping this on the actual reference machine surfaced two concrete constraints:

- **No NVIDIA GPU is present.** `nvidia-smi` doesn't exist on this machine, which has an Intel Arc A370M and an Intel Iris Xe instead.
- **Windows' WMI `AdapterRAM` field is unreliable.** It reported the identical, suspicious round number (10737418240 bytes) for two different GPUs — the well-known WMI DWORD-capping bug for modern GPU memory sizes.

Given that, GPU VRAM cannot be measured reliably on this machine today. System RAM, however, is reliably measurable cross-platform.

There is also no data source yet for how much memory a given model actually needs — no provider metadata, no benchmark-derived measurement.

---

# Decision

LAIR adds a hardware filter stage to candidate generation, after capability matching and before scoring.

- **`HardwareProfile`** describes the machine: `total_ram_gb`, `available_ram_gb`, and `gpu_vram_gb` (always `None` today — the field exists for forward compatibility once a reliable per-vendor detection method is added, but nothing populates it yet rather than guess).
- **`HardwareProvider`** is an abstract interface (mirrors `BaseProvider`), with one concrete implementation, `LocalHardwareProvider`, using `psutil` for RAM. Only one implementation exists — vendor-specific GPU detection (NVIDIA, AMD, Apple) stays future work, not built speculatively ahead of a reliable method.
- **`ResourceProfile`** describes what a model needs: `estimated_ram_gb`, resolved by `ResourceResolver` from the model id's parameter count (e.g. "32b"), the same heuristic-from-name spirit as `CapabilityResolver` (ADR-0004) — an explicit placeholder, not a measurement, meant to be replaced once real provider or benchmark-derived memory data exists.
- **`filter_by_hardware()`** keeps a model unless its estimated RAM requirement is known and exceeds available RAM. An unknown resource profile is kept, not rejected — consistent with ADR-0011 (Graceful Degradation): for a hard constraint, a wrong rejection is worse than a missed one.

This is a filter, not a scorer — it required no new `RoutingPolicy` field or weight.

A `DecisionProblem` bundling object was considered and not introduced. The filter slots into `RoutingEngine.route()` exactly the way capability matching already does — a plain function over the candidate list — so nothing forced that concept into existence yet.

---

# Alternatives Considered

## Attempt GPU VRAM Detection Anyway

Cons

- The only detection path available (WMI `AdapterRAM`) is confirmed unreliable on this exact machine
- A wrong VRAM reading is worse than no reading — it could wrongly reject a model that would fit, or wrongly accept one that won't, silently

## Score Hardware Fit Instead of Filtering It

Cons

- Conflates a hard constraint (will this crash or thrash) with a soft preference (is this the better model) — a model that literally cannot run should never be a low-scoring option, it should not be a candidate at all

---

# Consequences

Benefits

- LAIR can no longer recommend a model with a known memory requirement that exceeds what's actually available right now
- Confirmed against real, live numbers on this machine: ~32GB total RAM, ~1.6GB free after loading 6 models via LM Studio — exactly the scenario this feature exists to catch
- The `HardwareProvider` interface leaves room for real GPU detection later without changing anything above it

Trade-offs

- `ResourceProfile` is a rough heuristic, not a measurement — a model with an unusual naming convention or unusual quantization will be estimated incorrectly
- GPU-bound workloads get no hardware filtering at all yet, only RAM-bound ones

---

# Decision Summary

Hardware fit is enforced as a hard filter on candidates, using only what can be reliably measured today (system RAM) — not guessed (GPU VRAM) — and unknown resource data is treated as permissive, not restrictive.
