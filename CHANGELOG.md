# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and the project follows Semantic Versioning.

---

## [Unreleased]

### Added

- Capability Engine foundation
- Capability domain models
- Provider Registry
- AIModel domain model
- Capability Profile abstraction
- Capability Requirement abstraction
- `Task` domain model — transport-independent representation of work (ADR-0006)
- `RoutingPolicy` — single source of routing scoring weights (ADR-0008)
- `DecisionRecord` — auditable trace of a routing decision, replacing `RoutingDecision` (ADR-0007)
- `ExecutionPlan` / `ExecutionStep` — plan-shaped routing output (ADR-0009)
- Real `confidence` scoring on routing decisions, derived from the winner/runner-up score gap
- First test suite (pytest): unit coverage for the request analyzer, capability engine, capability resolver, model scorer, and decision record; API tests for `/health`, `/models`, and `/route`
- Benchmark Engine: `BaseProvider.complete()`, `BenchmarkRunner` (sequential, per-model graceful failure), `KnowledgeBase` (JSON-backed, read-only from scoring) — measures real latency/throughput and feeds it into routing via `RoutingPolicy.benchmark_weight` / `ScoreBreakdown.benchmark_score` (ADR-0005)
- `GET /benchmarks` — read-only listing of the latest benchmark result per model
- `scripts/run_benchmarks.py` — CLI entry point that triggers a benchmark run against all registered providers
- `run_id` on `BenchmarkResult`, grouping every result produced by one `BenchmarkRunner.run()` call
- `DecisionRepository` — persists every `DecisionRecord` to `logs/decisions.json`, the prerequisite for a future Learning Engine (ADR-0010)
- `task` and `requirements` fields on `DecisionRecord` — every persisted decision now retains what prompt and requirements produced it, not just the scored candidates
- Hardware-aware filtering: `app/hardware/` package — `HardwareProfile`, `HardwareProvider`/`LocalHardwareProvider` (system RAM via `psutil`; GPU VRAM intentionally left unmeasured — unreliable on this reference machine), `ResourceProfile`/`ResourceResolver` (heuristic model-size estimate from the id), `filter_by_hardware()` — models that can't fit in available RAM are excluded from candidates before scoring (ADR-0012)
- `psutil` dependency for hardware detection
- `docs/adr/ADR-0005-benchmark-driven-routing.md`, `docs/adr/ADR-0010-decision-persistence.md`, `docs/adr/ADR-0011-graceful-degradation.md`, and `docs/adr/ADR-0012-hardware-aware-filtering.md`
- `ModelMetadata` — provider-agnostic model metadata (`app/providers/model_metadata.py`); `LMStudioProvider` now reads LM Studio's native `/api/v0/models` API (real vision/embedding type, tool-use capability, quantization, loaded state, context length), with graceful fallback to the original `/v1/models` call when unavailable (ADR-0013)
- `docs/adr/ADR-0013-provider-metadata-grounding.md`

### Changed

- Refactored `BaseProvider` to return `AIModel` objects instead of raw dictionaries.
- Refactored LM Studio provider to use the domain model.
- Refactored `ModelRegistry` to use the new `ProviderRegistry`.
- Expanded application configuration for future providers and routing.
- **Breaking:** `/route` response is now plan-shaped (`plan.steps`, `plan.decision`) instead of a flat `selected_model`/`provider`/`confidence`/`breakdown` body.
- Capability scoring now reads weights from `RoutingPolicy.capability_weights` instead of the standalone `CAPABILITY_WEIGHTS` constant and `Settings` fields — same values, single source of truth, not a scoring regression.
- `CapabilityResolver`/`ResourceResolver` now ground VISION/EMBEDDING/TOOL_USE/`context_window`/resource estimates in real LM Studio metadata when available, falling back to the original heuristics otherwise — REASONING/CODING/TRANSLATION/SUMMARIZATION remain heuristic (no data source exists for them).
- `AIModel.loaded` now reflects the provider's real reported state instead of always being hardcoded `True`; not-loaded models are excluded from routing candidates.

### Fixed

- `/route` no longer crashes with a `ValidationError` (the selector built a `RoutingDecision` with fields, `score`/`reasons`, that didn't exist on the class).
- `requirements.txt` was UTF-16 encoded, breaking `pip install` on most environments; re-saved as UTF-8.
- `KnowledgeBase` no longer crashes `/route` when a stored benchmark record predates a `BenchmarkResult` schema change (e.g. the new `run_id` field) — unreadable records are now skipped and logged instead of raising.
- `/route` no longer mislabels unrelated validation errors as "no suitable model found" — it caught bare `ValueError`, which `pydantic.ValidationError` subclasses; now catches the specific `NoCandidateModelsError` it's meant to.
- `CapabilityProfile.context_window` had been `None` for every model since Milestone 1 (nothing ever set it), meaning `ModelScorer.context_window_score` silently contributed `0.0` to every routing decision — now populated from real provider metadata when available.
- `filter_by_hardware()` was checking an already-loaded model's estimated memory requirement against currently-*free* RAM, wrongly excluding it — a loaded model's memory is already allocated and it's proven to be running right now, so the RAM-fit check only makes sense for a model that would need fresh allocation to load. Surfaced live only once real loaded-state data existed (this milestone); already-loaded models are now always kept.

### Removed

- `app/router/` — empty, unused duplicate of `app/routing/`.
- `app/routing/capability_weights.py` — migrated into `RoutingPolicy` defaults.
- `Settings.STREAMING_WEIGHT` / `CAPABILITY_WEIGHT` / `CONTEXT_WINDOW_WEIGHT` — migrated into `RoutingPolicy`.

---

## [0.1.0-alpha] - 2026-07-13

### Added

- Initial FastAPI application structure
- LM Studio provider
- Provider abstraction layer
- Model registry
- Health API
- Models API
- Architecture documentation
- Engineering handbook
- Product vision
- Project charter
- Routing engine design
- Benchmarking design
- ADR framework
- RFC framework
- Research framework
- Innovation backlog
- Repository governance
- GitHub Release `v0.1.0-alpha`