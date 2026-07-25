# LAIR Innovation Plan 2026

**Project:** LAIR — Local AI Intelligence Router
**Status:** All 20 entries (I-01–I-19, Waves 1–5) implemented and merged to `main` as of 2026-07-25. This plan's Implementation Sequence is complete; see `docs/innovation_backlog.md` for what's next, and the honest-scope notes on I-11/I-16/I-19 below for follow-up work named but not yet done.
**Version:** 2.0
**Created:** 2026-07-22 | **Updated:** 2026-07-25 (added §1.7–§1.10, entries I-16–I-19, expanded I-11, Wave 5; 2026-07-25: all 20 entries shipped, moved here from a stray repo-root copy so this file — the one `CLAUDE.md` actually points to — is current)
**Owner:** Najam (Nazmul Mustufa Farooquee)

---

## Implementation Status (2026-07-25)

Every entry below shipped, in order, across 8 commits on `main`:

| Wave | Entries | Status |
|---|---|---|
| 1 | I-13, I-01, I-05, I-04 (rules phase) | Shipped |
| 2 | I-02, I-03 (ADR-0016), I-14, I-10 | Shipped |
| 3 | I-07, I-04 (model-assisted phase), I-06 (RFC-0001, ADR-0018), I-08 (ADR-0019), I-09, I-17 (ADR-0017) | Shipped |
| 4 | I-18 (RFC-0002, ADR-0020), I-11, I-12, I-15 | Shipped |
| 5 | I-16 (ADR-0021, infrastructure only — execution deferred), I-19 (RFC-0003, Phase 1a only — real-model compression deferred) | Shipped (honestly scoped) |

Two entries shipped with an explicit, documented scope reduction rather than a fabricated full implementation:

- **I-16 (Streaming-Aware Routing):** the hardware SSD-benchmark signal, registry schema (`streamable`, `streaming_viability`), and routing-side allowance/labeling logic are real and tested. The actual streaming *execution* path needs a llama.cpp-direct provider that doesn't exist yet (LM Studio doesn't expose mmap/streaming knobs) — deferred to the future Multi-Provider milestone (v0.5), per ADR-0021.
- **I-19 (LAIR Compact Models):** Phase 1a (validating the tensor-train/MPO compression math on synthetic matrices, `scripts/compactify/`) is done and shipped a real, honest finding about tensorization sensitivity. Phase 1b (applying it to a real small open model, with quality benchmarks) is named future work, not yet started — see RFC-0003.

209 net new tests were added across all five waves (test count grew from 87 to 432).

---

# Purpose

This document is the strategic and technical master plan for LAIR's next development cycle. It has three audiences:

1. **The maintainer** — a durable record of research findings and decisions.
2. **Contributors** — context for why each feature exists and how it should be built.
3. **Claude Code** — an executable plan. Each innovation entry includes acceptance criteria. When instructed to "implement the next item," follow the Implementation Sequence at the end of this document and the engineering workflow in `CLAUDE.md` (RFC → ADR → Implementation → Tests → Benchmark).

## The Two Missions

**Mission A — Affordability.** Cloud LLM APIs are expensive and metered. LAIR should let anyone do 90%+ of their AI work on models they already own, with cloud usage as a tightly budgeted exception, not the default.

**Mission B — Accessibility.** Most of the world does not own a 64GB workstation. LAIR must deliver a great experience on 8–16GB laptops, including machines with no GPU at all. "Runs well on the laptop you already have" is the promise.

Everything in this plan serves one or both missions.

---

# Part 1 — Research Findings (State of the World, mid-2026)

These findings ground the plan in what is actually possible today. Sources listed in Appendix A.

## 1.1 MoE + quantization changed the hardware math

The single most important shift for Mission B: **Mixture-of-Experts (MoE) models with small active-parameter counts run large-model quality on small hardware.** Qwen3-35B-A3B has 35B total parameters but only ~3B active per token; with expert-offloading (llama.cpp's expert-pinning, exposed in LM Studio as "Force Model Expert Weights onto CPU"), a 12GB GPU runs a 35B-class model at ~60 tok/s, and even 6–8GB GPUs can run it. LAIR's current portfolio already includes A3B/A4B MoE models — the plan should make MoE + expert-offload a first-class routing concept, not an accident of model choice.

Quantization rules of thumb the router should encode:
- Q4_K_M is the sweet spot: ~75% memory reduction vs FP16, near-indistinguishable output for most tasks.
- Within a fixed memory budget, a **larger model at Q4 usually beats a smaller model at Q8**.
- KV cache grows with context length and competes with weights for memory; context length is a routing variable, not a constant. Low-VRAM guidance: cap context at 4096 by default on ≤8GB machines and let the router raise it only when the task needs it.
- CPU-only inference is viable: a modern multi-core CPU with fast RAM runs 3–13B Q4 models at usable speeds. DDR5 bandwidth matters as much as capacity.

## 1.2 The small-model landscape is genuinely good now

For the hardware-tier portfolios (Innovation I-02), the current consensus picks:

| RAM tier | Recommended models (mid-2026) |
|---|---|
| 8GB (entry) | Phi-4-mini 3.8B (~3GB at Q4, best small reasoner, CPU-friendly); Gemma 3 4B / Gemma 3n E4B (multimodal, 140+ languages, selective activation → 8B capacity at ~4B footprint); Qwen3.5-4B (Apache 2.0, 262K context, multilingual, native image understanding); Llama 3.2 3B (general chat); SmolLM3-3B (fully open, /think dual-mode) |
| 16GB (standard) | Qwen3 7–8B (best small coder), Llama 3.3 8B (best all-rounder), Phi-4 14B (84.8% MMLU on a 12GB GPU), DeepSeek-R1-Distill small variants for reasoning |
| 32GB+ (enthusiast) | Current LAIR portfolio (Qwen3.6 35B A3B, Gemma 4 26B A4B, DeepSeek-R1 Distill 32B, Qwen2.5-VL 7B, Qwen3 8B) |

Two capabilities worth exploiting in routing: **dual-mode reasoning** (Qwen3/SmolLM3 `/think` vs `/no_think` — the router can request thinking only for hard tasks) and **selective activation** (Gemma 3n) for multimodal on tiny machines.

## 1.3 LM Studio already provides the memory-management primitives

Do not reinvent these — orchestrate them:

- **JIT loading:** first request to a model loads it automatically.
- **Idle TTL:** `ttl` field in the request payload controls how long a model stays loaded after last use (default 60 min). LAIR can set short TTLs for rarely-used specialists and long TTLs for the fast assistant.
- **Auto-Evict:** LM Studio unloads the previous JIT model before loading a new one (max 1 JIT model in memory) — this is effectively single-slot scheduling at the provider level; LAIR's scheduler should cooperate with it, not fight it.
- **Speculative decoding:** pass `draft_model` in the request payload to pair a big model with a tiny same-family draft model (e.g., DeepSeek-R1-Distill-7B + 0.5B draft) for faster generation at identical quality. This is a per-request API parameter — the router can enable it dynamically.

## 1.4 Routing research validates the cascade/triage approach

The academic literature (FrugalGPT, RouteLLM, HybridLLM, AutoMix, IRT-Router, and 2026 cascade frameworks) converges on findings directly applicable to LAIR:

- **Difficulty-aware routing works.** RouteLLM's learned routers cut cost ~85% on MT-Bench while retaining ~95% of the strong model's quality, sending only ~14% of queries to the strong model. Numbers are benchmark-specific but prove the mechanism.
- **Cascades (try cheap, escalate on failure) reduce cost further** but add latency on escalated queries; the 2026 refinement is to pre-route *predictably hard* queries directly to the strong model and cascade only the ambiguous middle.
- **A 2026 survey frames the design space** on three axes: when the decision is made (pre-request / during / post-response), what feeds it (query features, model metadata, past performance), and how (rules, classifiers, cascades). Well-designed routing can *beat the single best model* by exploiting specialization — routing raises quality, not just savings.
- Practical layering used in production: cheap rules first → embedding-similarity or small-classifier triage → cascade with self-verification as safety net. LAIR should implement exactly this stack (I-04, I-06).

## 1.5 A fully local voice stack is mature

Whisper-family STT (faster-whisper: 4× faster GPU, 2× CPU via CTranslate2/INT8; whisper.cpp for pure CPU), wake-word detection (OpenWakeWord, Porcupine), and modern local TTS (Kokoro-82M: Apache 2.0, ~2–3GB VRAM or CPU-capable, near-cloud quality; Piper archived Oct 2025 but functional; Chatterbox/XTTS for cloning) make a **fully offline voice interface** achievable with 1–2s end-to-end latency on a mid-range GPU and 5–10s on CPU. Whisper large-v3 achieves <3% WER on clean English, matching cloud services, and handles many languages — synergistic with Mission B's global audience.

## 1.6 Hybrid local/cloud economics

Real-world case studies show 60–83% cost reductions by moving high-volume easy traffic to local models and reserving cloud APIs for genuinely hard tasks. The pattern LAIR should productize: local by default, cloud as a *budgeted escalation tier* with a hard monthly cap and per-request transparency.

---

---

## 1.7 Layer streaming: big models on small RAM (with honest limits)

Weight streaming lets a model larger than RAM run by keeping weights on SSD and pulling them in as needed. The spectrum, from proven-but-slow to practical:

- **Pure layer-by-layer streaming (AirLLM):** genuinely runs 70B models on ~4GB, but a single response takes 15–30 minutes and hammers CPU + SSD. Proof of concept, not a daily driver.
- **mmap + OS paging (llama.cpp default):** weights are memory-mapped; the OS pages them from disk on demand. Works today; unpredictable when the model far exceeds RAM.
- **Predictive prefetch + LRU caching (ssd-llm, oLLM):** the practical frontier. Issue `madvise(MADV_WILLNEED)` for the *next* layer while the current one computes; pin hot layers (embeddings, output head) in an LRU cache; evict finished layers with `MADV_DONTNEED`. Like buffering the next scene of a movie. Modern PCIe 5.0/6.0 SSDs (10–20 GB/s) make this increasingly viable, and MoE models (few active params per token) are the best-case workload.

**Implication for LAIR:** LAIR shouldn't reimplement inference — but it *should* know each machine's streaming capability (SSD speed, RAM headroom) and route accordingly: offer "slow but possible" as an explicit, explained tier rather than "model too large, refuse."

## 1.8 Quantization beyond Q4: mixed precision and the KV cache

Two techniques matter beyond plain Q4_K_M:

- **Mixed-precision weights:** keep the most sensitive layers (typically first and last) at higher precision and compress the middle harder. MLX and llama.cpp ecosystems both support per-layer bit allocation; quality loss is far smaller than uniform low-bit quantization at the same size.
- **KV-cache quantization:** the conversation's memory footprint grows linearly with context and often dominates on long chats. INT8 KV quantization is now near-free (reconstruction error <0.004 in 2026 CUDA work). The 2026 research frontier is *adaptive* allocation — RateQuant (rate-distortion-optimal per-head bits), PM-KVQ (progressive precision for long chain-of-thought), KVmix (AAAI-26, gradient-based layer importance), and Huffman-style per-token-importance schemes for on-device use. Exactly the "spend bits where they matter" principle.

**Implication for LAIR:** quantization choice becomes a *routing dimension*, not just a download decision. The registry should understand a model's KV-cache options and pick configurations that fit the machine and the conversation length.

## 1.9 Persistent agent memory is now a first-class field

2026 consensus: memory is an architectural component, not a hack. The ecosystem — Mem0 (51k+ stars; 3-tier user/session/agent scopes over vector+graph+KV), Letta/MemGPT (OS-style memory hierarchy), Zep/Graphiti (temporal knowledge graphs), Cognee (local-first, privacy-critical), agentmemory & Supermemory (coding agents), claude-mem — all converge on the same key insight: **retrieve only the relevant slices and inject those**. Benchmarked systems stay under ~7k tokens per retrieval versus 25k+ for full-history stuffing. Local embedding models (all-MiniLM-L6-v2) make this fully offline and free. Hard open problems: cross-session identity, temporal abstraction, staleness.

**Implication for LAIR:** LAIR sits between every client (VS Code, voice, CLI) and every model — the ideal choke point to own project memory once, locally, and make it portable across tools. Small retrieval slices are also exactly what small-context, low-RAM machines need. Mission A and B solve each other here.

## 1.10 Quantum-inspired tensor-network compression (and the honest word on real quantum)

Two things wear the word "quantum" — they must not be confused:

- **Real quantum hardware:** advancing (IBM ran Cayley unitary adapters inside Llama 3.1 8B on a 156-qubit processor in 2026, improving perplexity 1.4%), but it requires lab-grade quantum computers. For LAIR's audience this is a watch-list item, not a foundation. We do not build on it.
- **Quantum-inspired tensor networks — runs on ordinary laptops today:** Multiverse Computing's CompactifAI decomposes attention/MLP weight matrices into Matrix Product Operators (MPOs — math from quantum many-body physics), truncating redundant correlations. A tunable "bond dimension" controls the squeeze. A brief **"healing" retrain** recovers most lost accuracy. Results: up to ~93–95% size reduction with ~90%+ accuracy retention; Llama-2 7B to ~30% size recovering >90% accuracy; their compressed 70B runs on plain Intel Xeon CPUs; HyperNova 60B (Feb 2026) is a 50%-compressed derivative of GPT-OSS-120B. Follow-on open research (Minima, 2026) reproduces the pipeline, and mature open-source tensor libraries (quimb, TensorLy) implement the underlying MPO decomposition.

**The catch, stated honestly:** the healing retrain needs real GPU muscle — beyond a student laptop. So the viable open-source architecture is **compress-once, run-everywhere**: compression + healing happen once on capable hardware (maintainers, community, donated compute), and the small healed model is published for anyone to run locally forever. Multiverse sells this via cloud; LAIR's differentiated mission is bringing the *results* of quantum-inspired compression to local machines, free.


# Part 2 — Innovation Entries

Format follows `docs/innovation_backlog.md`. Each entry is implementation-ready: it includes design notes and acceptance criteria for Claude Code.

---

## I-01 — Savings Dashboard & Cost Transparency

**Status:** 💡 Proposed | **Priority:** High | **Category:** Developer Experience | **Target:** 0.3

**Description.** Annotate every response with the model that answered and the estimated cloud-equivalent cost avoided. Maintain running totals (day/month/all-time) exposed at `GET /v1/lair/savings` and in response metadata.

**Design notes.**
- Maintain a small pricing table in `configs/cloud_pricing.yaml` (per-1M input/output token prices for GPT-4-class, Claude-class, budget-class). Map each local model to a "cloud equivalent class."
- Count tokens from the execution engine's existing logging (request/response token counts already logged).
- Store totals in a local SQLite or JSON store under `logs/`.

**Acceptance criteria.**
- [ ] Every `/v1/chat/completions` response includes `lair_meta.estimated_savings_usd` and `lair_meta.model_used`.
- [ ] `GET /v1/lair/savings` returns day/month/lifetime totals.
- [ ] Pricing table is user-editable; missing mappings degrade gracefully (savings shown as null, never crash).
- [ ] Unit tests for the cost calculator with at least 3 pricing scenarios.

---

## I-02 — Hardware-Aware Onboarding (`lair doctor` + tiered portfolios)

**Status:** 💡 Proposed | **Priority:** Critical | **Category:** Accessibility | **Target:** 0.3

**Description.** On first run (or via `python -m lair doctor`), profile the machine (total/free RAM, VRAM, GPU model, CPU cores, disk space) and recommend a model portfolio matched to a hardware tier. Offer one-command setup that configures the registry for that tier.

**Design notes.**
- Tiers: ENTRY (≤8GB RAM), STANDARD (16GB), ENTHUSIAST (32GB+), CPU_ONLY (no usable GPU). Portfolios per §1.2 research findings; store as `configs/portfolios/{tier}.yaml`.
- Use `psutil` for RAM/CPU; GPU detection via `nvidia-smi` parse, Apple Silicon via platform detection (unified memory = treat RAM as VRAM), fallback to CPU_ONLY.
- Doctor also validates: LM Studio installed and reachable, port free, Python version.
- Do NOT auto-download models without confirmation; print the LM Studio search terms / download instructions per model.

**Acceptance criteria.**
- [ ] `doctor` command prints hardware profile, assigned tier, portfolio recommendation, and any environment problems with fixes.
- [ ] Registry can be initialized from a tier portfolio file in one command.
- [ ] CPU_ONLY tier produces a working configuration (small models, conservative context).
- [ ] Tests mock hardware profiles for all four tiers.

---

## I-03 — Quantization-Aware Registry & Graceful Degradation

**Status:** 💡 Proposed | **Priority:** Critical | **Category:** Model Intelligence / Accessibility | **Target:** 0.3–0.4

**Description.** Treat each quantization of a model as a distinct registry entry with its own memory footprint, speed, and quality score. The router selects not just *which model* but *which quant fits currently free memory*, degrading to a smaller quant (or smaller model) under pressure instead of failing.

**Design notes.**
- Registry schema additions: `quant` (e.g., Q4_K_M), `est_memory_gb`, `min_context`, `max_context`, `moe` (bool), `active_params_b`, `expert_offload_supported` (bool).
- Memory estimation formula: weights + KV cache (scales with context) + overhead. Encode the §1.1 rules: prefer larger-model-Q4 over smaller-model-Q8 within a budget; cap default context at 4096 on ENTRY tier.
- Hardware validation stage of the routing pipeline consults *live* free RAM/VRAM (psutil / nvidia-smi), not static config.
- MoE models with expert-offload get a memory bonus in scoring (they fit where dense peers don't).

**Acceptance criteria.**
- [ ] Registry supports multiple quant entries per base model.
- [ ] Router selects a quant that fits live free memory; integration test simulates memory pressure and verifies degradation instead of OOM.
- [ ] Routing explanation names the quant chosen and why (e.g., "Q4_K_M selected: Q8 needs 22GB, 14GB free").

---

## I-04 — Task Complexity Triage

**Status:** 💡 Proposed | **Priority:** Critical | **Category:** Routing Intelligence | **Target:** 0.3

**Description.** Add a difficulty dimension to capability extraction. A cheap triage stage rates each request's complexity (1–5); simple requests route to the smallest viable model, complex ones to specialists. Grounded in RouteLLM/HybridLLM findings (§1.4).

**Design notes.**
- Phase 1 (rules): heuristics — prompt length, code-block presence, keywords ("prove", "step by step", "refactor entire"), conversation depth. Zero cost.
- Phase 2 (model-assisted): the fast-assistant model classifies with a ~50-token prompt returning JSON `{complexity: 1-5, task_type}`. Cache classifications by prompt hash.
- Complexity feeds the composite score as a new factor; also gates dual-mode reasoning: request `/think` mode (Qwen3/SmolLM3) only for complexity ≥4.
- Log predicted complexity with each decision so the future Learning Engine (v0.6) can calibrate it against outcomes.

**Acceptance criteria.**
- [ ] Triage stage inserted between Capability Extraction and Candidate Discovery in the pipeline.
- [ ] Rules-based classifier ships first with unit tests on ≥20 example prompts.
- [ ] Routing explanation includes complexity and its effect on selection.
- [ ] Toggleable via config (off = current behavior).

---

## I-05 — Single-Slot Model Scheduler (swap minimization)

**Status:** 💡 Proposed | **Priority:** High | **Category:** Accessibility / Performance | **Target:** 0.3

**Description.** On constrained machines only one model fits; swaps are the dominant cost. Add (a) a stickiness bonus for the currently loaded model when it is "good enough," and (b) request batching by capability to minimize swaps. Cooperate with LM Studio's Auto-Evict and TTL rather than duplicating them.

**Design notes.**
- Stickiness: composite-score bonus for the loaded model, sized so it wins ties and near-ties but never overrides a hard capability mismatch (vision task ≠ text model).
- Set per-request `ttl` intelligently: long TTL for the tier's generalist, short TTL for specialists.
- Optional queue mode (config flag): hold requests briefly (e.g., 2s window) and group by target model.
- Enable speculative decoding automatically where a compatible draft model exists in the registry (pass `draft_model` in the payload) — free speed on the same hardware.

**Acceptance criteria.**
- [ ] Sticky bonus implemented, configurable weight, covered by routing tests.
- [ ] TTL set per request based on model role.
- [ ] Benchmark script demonstrates reduced swap count on a simulated mixed workload.
- [ ] Draft-model pairing table in registry; speculative decoding activates when available.

---

## I-06 — Hybrid Cloud Escalation with Budget Cap ("cost firewall")

**Status:** 💡 Proposed | **Priority:** High | **Category:** Routing Intelligence / Affordability | **Target:** 0.5

**Description.** Optional cloud tier (OpenAI-compatible APIs, Anthropic, DeepSeek) used only when (a) the task exceeds local capability (complexity 5, context overflow, or cascade failure) AND (b) the user's hard monthly budget (e.g., $5) has headroom. Off by default. Local-first is non-negotiable (see CLAUDE.md constraint #1).

**Design notes.**
- Implement as a Provider like any other, but flagged `cloud=true`; routing applies budget check + escalation policy before ever considering it.
- Cascade option: local model answers first; a lightweight local verifier (fast assistant self-check, per AutoMix) decides escalation. Pre-route only clearly-hard queries directly to cloud (per 2026 cascade research) to avoid wasted local calls.
- Spend tracking shares the I-01 ledger. When cap is hit: fall back to best-effort local + honest note in `lair_meta`.
- Privacy: log clearly (and surface in explanation) whenever a prompt leaves the machine.

**Acceptance criteria.**
- [ ] Cloud providers configurable via env/config; disabled unless explicitly enabled with a budget.
- [ ] Hard cap enforced with tests (simulate cap exhaustion mid-month).
- [ ] Every cloud-routed response marked in `lair_meta.routed_to_cloud=true` with reason.
- [ ] RFC + ADR written before implementation (this is an architectural change).

---

## I-07 — Semantic Response Cache

**Status:** 💡 Proposed | **Priority:** Medium | **Category:** Performance / Affordability | **Target:** 0.4

**Description.** Embedding-based local cache: if a new request is ≥ threshold similarity to a past one (and context-compatible), serve the cached answer at zero token/GPU cost.

**Design notes.**
- Small local embedding model (e.g., a MiniLM-class ONNX model on CPU) + SQLite with vector extension or simple numpy index; keep dependencies light.
- Conservative defaults (high threshold, exact-match tier first); per-request opt-out; TTL on cache entries; never cache when conversation history differs materially.

**Acceptance criteria.**
- [ ] Cache hit path adds <50ms overhead; miss path adds <20ms.
- [ ] `lair_meta.cache_hit=true` on served-from-cache responses.
- [ ] Config: enable/disable, threshold, max entries, TTL.

---

## I-08 — RAG-Lite Document Pipeline (PDFs & research on small machines)

**Status:** 💡 Proposed | **Priority:** High | **Category:** Model Intelligence / Accessibility | **Target:** 0.5

**Description.** Small-context local models can't swallow a 200-page PDF — and don't need to. Local ingestion (chunk + embed once), retrieval of relevant chunks per question, vision-model pass for scanned pages. A 4B model on an 8GB laptop then answers questions over huge documents.

**Design notes.**
- Reuse I-07's embedding infrastructure. `POST /v1/lair/documents` to ingest; retrieval injected transparently when a conversation references an ingested doc.
- Scanned-PDF pages route through the vision model (registry capability: vision) for OCR-style extraction before embedding.
- Keep it "lite": no external vector DB dependency by default.

**Acceptance criteria.**
- [ ] Ingest a 100+ page text PDF and answer section-specific questions correctly with a ≤4B model in tests.
- [ ] Retrieval context fits the target model's context budget (respects I-03 limits).
- [ ] All processing local; no network calls.

---

## I-09 — Context Compression for Long Chats

**Status:** 💡 Proposed | **Priority:** Medium | **Category:** Performance | **Target:** 0.5

**Description.** When conversation history approaches the selected model's context limit, the fast assistant summarizes older turns locally before forwarding. Locally, "token savings" means fitting small context windows at all — and smaller KV cache = less RAM (§1.1).

**Acceptance criteria.**
- [ ] Triggered automatically at a configurable context-fill threshold (default 80%).
- [ ] Recent N turns always preserved verbatim; summary marked in forwarded prompt.
- [ ] Test: 50-turn conversation stays functional on a 4K-context model.

---

## I-10 — Language-Aware Routing

**Status:** 💡 Proposed | **Priority:** Medium | **Category:** Routing Intelligence / Accessibility | **Target:** 0.4

**Description.** Detect query language (fast local detection) and factor each model's per-language strength into scoring. A user asking in Hindi, Arabic, or Portuguese silently gets the model strongest in their language (Qwen: 100+ languages; Gemma 3n: 140+). Directly serves the global-audience mission.

**Acceptance criteria.**
- [ ] Registry gains `language_strengths` metadata.
- [ ] Language detected per request (lightweight lib, e.g., lingua/fasttext); factored into scoring with explanation.
- [ ] Tests cover at least 5 languages.

---

## I-11 — Voice Interface (fully local) — EXPANDED

**Status:** 💡 Proposed | **Priority:** High (promoted from Medium, 2026-07-25) | **Category:** Accessibility / Developer Experience | **Target:** 0.6

**Description.** Speak to LAIR, hear answers — fully offline, no subscription, nothing leaves the laptop. Stack per §1.5: faster-whisper (STT, INT8 on CPU or GPU) → LAIR routing → Kokoro-82M (TTS, Apache 2.0, CPU-capable, near-cloud quality). Optional wake word ("Hey LAIR") via OpenWakeWord. Round-trip latency ~1–2s on mid-range hardware.

**Why this is a mission feature, not a gimmick.**
- **Language access:** Whisper is strongly multilingual. A student in Karachi or São Paulo speaks in their own language; detected language flows into I-10 so LAIR routes to the model strongest in that language and can answer in kind.
- **Accessibility:** for people who struggle with typing, are visually impaired, or think best out loud, voice is access, not convenience.
- **Continuity:** voice sessions read/write the same Persistent Project Memory (I-18) as IDE sessions — talk through an idea in the morning, code against it in VS Code in the afternoon.

**Design notes.**
- Ship as an optional extra (`pip install lair[voice]`) so the core stays light; components load lazily.
- Endpoints: `POST /v1/audio/transcriptions` and `POST /v1/audio/speech` (OpenAI-compatible, so existing voice clients work), plus a `lair voice` CLI loop; later a minimal web UI with push-to-talk.
- Model sizes by tier (I-02): whisper tiny/base on ENTRY/CPU_ONLY, small/medium on STANDARD+. Kokoro runs everywhere.
- Interruption/barge-in support in the loop (stop TTS when the user starts speaking).
- Voice replies should prefer concise routing (triage bias toward fast models for conversational turns; escalate only for hard questions).
- Note: Piper is archived (Oct 2025); Kokoro is the default voice.

**Acceptance criteria.**
- [ ] Round-trip voice query works offline on STANDARD tier hardware in <3s; degraded-but-working on CPU_ONLY.
- [ ] Voice components load lazily; zero overhead when unused.
- [ ] Language of the spoken query flows into I-10 routing; reply language matches query language.
- [ ] Wake-word mode optional and off by default (privacy: mic stays closed unless enabled).
- [ ] Voice sessions attach to a project memory scope (I-18) when one is active.

---

## I-12 — Community Capability Database (opt-in)

**Status:** 💡 Proposed | **Priority:** High | **Category:** Benchmarking / Network Effects | **Target:** 0.6

**Description.** Benchmarking is expensive on weak hardware. Users opt in to share anonymized benchmark results tagged by hardware profile; new users inherit routing scores measured by similar machines. Crowdsources the Benchmark Engine; improves with adoption.

**Design notes.**
- Strictly opt-in, anonymized (hardware tier + model + scores only; never prompts). Static JSON snapshots fetched from the GitHub repo initially — no server infrastructure needed for v1.
- Provenance tagging (below) marks these scores COMMUNITY vs locally MEASURED.

**Acceptance criteria.**
- [ ] `configs/community_scores/` snapshot format defined + loader.
- [ ] Local measurements always override community scores.
- [ ] Contribution export produces a shareable, anonymized JSON.

---

## I-13 — Provenance-Tagged Explanations

**Status:** 💡 Proposed | **Priority:** High | **Category:** Explainability | **Target:** 0.3

**Description.** Every factor in a routing explanation carries a provenance tag: MEASURED (local benchmark), COMMUNITY (I-12), DECLARED (registry metadata), HEURISTIC (rule/default). Users know whether "coding score 96" was measured on their machine or copied from a leaderboard. LAIR's clearest differentiator — no existing router does this.

**Acceptance criteria.**
- [ ] Explanation schema (Pydantic) includes per-factor provenance.
- [ ] All existing scoring factors tagged; tests assert no untagged factor can be emitted.

---

## I-14 — One-Command IDE Integration (`lair install`)

**Status:** 💡 Proposed | **Priority:** High | **Category:** Developer Experience | **Target:** 0.4

**Description.** Auto-write client configs pointing VS Code (Continue, Cline), Cursor, Windsurf, Zed, and Claude Code at LAIR's endpoint. Removes the biggest onboarding friction.

**Acceptance criteria.**
- [ ] `lair install --client continue` (etc.) writes/patches the correct config file, backing up originals.
- [ ] `lair install` with no args detects installed clients and offers choices.
- [ ] Uninstall restores backups.

---

## I-15 — Battery & Thermal Awareness

**Status:** 💡 Proposed | **Priority:** Low | **Category:** Accessibility | **Target:** 0.6

**Description.** On battery power (psutil), bias routing toward smaller/faster models; optionally shorten TTLs. Laptops are the primary audience.

**Acceptance criteria.**
- [ ] Power state read cross-platform; scoring factor + explanation entry; config toggle.

---

## I-16 — Streaming-Aware Routing (big models on small RAM)

**Status:** 💡 Proposed | **Priority:** High | **Category:** Accessibility / Efficiency | **Target:** 0.6–0.7

**Description.** Per §1.7, models larger than RAM can run via mmap + predictive prefetch from SSD — slowly, but they run. Today every tool simply refuses; LAIR should instead *know* the machine's streaming capability and offer "slow but possible" as an explicit, explained routing tier. A student with 8GB RAM and a fast SSD can still get a 30B-class answer for the rare question that truly needs one — they just wait, knowingly.

**Design notes.**
- `lair doctor` (I-02) gains an SSD benchmark (sequential read GB/s) and computes a per-machine `streaming_viability` score; stored in the hardware profile.
- Registry entries gain `min_ram_resident` and `streamable: true/false` fields; routing treats a streamable-but-oversized model as available at a heavy latency penalty, surfaced in the explanation ("via SSD streaming, est. 4–8× slower").
- Backend reality: LM Studio doesn't expose streaming knobs, so this tier initially targets a llama.cpp-direct provider (mmap default; `--no-mmap`/`--mlock` tuning per §1.7) — natural companion to the Multi-Provider milestone (v0.5). MoE models are the priority streamable class (few active params/token).
- Never route to streaming silently: complexity triage (I-04) must justify it, and the user can cap max latency in config.
- Watch-list: ssd-llm-style `madvise` prefetch daemons; upstream llama.cpp/MLX out-of-core work.

**Acceptance criteria.**
- [ ] Hardware profile includes measured SSD read speed + streaming_viability.
- [ ] Registry schema supports streamable models (ADR — schema change).
- [ ] Routing explanation clearly labels streaming picks with a latency estimate; config knob `max_acceptable_latency` gates them.
- [ ] Benchmark: one oversized MoE model demonstrably answers on an 8–16GB machine via streaming, with recorded tok/s.

---

## I-17 — Advanced Quantization Intelligence (mixed precision + KV cache)

**Status:** 💡 Proposed | **Priority:** High | **Category:** Efficiency | **Target:** 0.4–0.6

**Description.** Extend I-03's quantization awareness from "which weight quant" to the full 2026 toolkit (§1.8): prefer mixed-precision builds where available, and treat **KV-cache quantization** as a routing/configuration dimension — the KV cache is what actually blows up memory in long chats on small machines.

**Design notes.**
- Registry gains per-variant fields: `weight_scheme` (e.g., Q4_K_M, mixed W4/W8), `kv_cache_options` (fp16/int8/q4), and measured quality deltas where known.
- Fit-to-memory logic (I-03) computes *weights + KV at requested context* instead of weights alone; on ≤8GB machines LAIR can choose int8 KV to double usable context, and say so in the explanation ("int8 KV cache: fits 8k context in your 6GB budget, ~negligible quality cost").
- Context compression (I-09) and this entry are complementary: quantize what you keep, compress what you summarize.
- Watch-list (not build-now): adaptive per-token/per-head allocation — RateQuant, PM-KVQ, KVmix (AAAI-26) — adopt when runtimes expose it.

**Acceptance criteria.**
- [ ] KV-cache memory model added to fit calculations; tests cover context-length scenarios on each tier.
- [ ] Where the backend exposes KV quant settings, LAIR sets them per request/model and tags the explanation.
- [ ] Portfolio files can recommend mixed-precision builds per tier.

---

## I-18 — Persistent Project Memory (local, private, portable)

**Status:** 💡 Proposed | **Priority:** Critical | **Category:** Continuity / Differentiator | **Target:** 0.5–0.6

**Description.** The pain: every new chat, every tool switch, loses context — re-explaining your project to your own computer. Per §1.9, LAIR sits between *every* client (VS Code, Cursor, voice, CLI) and every model, making it the natural single owner of memory. A project-scoped local store remembers decisions, preferences, and facts across sessions and across tools; at request time LAIR retrieves only the relevant slices and injects them — which keeps injections small enough for low-RAM machines with short contexts. Continuity (Mission A's daily usefulness) and accessibility (Mission B's small budgets) solve each other.

**Design notes.**
- Storage: local SQLite + embedded vector index (all-MiniLM-L6-v2 embeddings — free, offline, tiny). No cloud, no telemetry. One store per project scope; scopes selected via header/config/`lair` CLI.
- Memory lifecycle: extract candidate memories from exchanges (facts, decisions, preferences) → dedupe/update → retrieve top-k by relevance at request time, hard-capped by a token budget per tier (e.g., ≤1.5k tokens on ENTRY, ≤4k on ENTHUSIAST).
- Reuses the same embedding machinery as the semantic cache (I-07) and RAG-lite (I-08) — build once, use three ways.
- Transparency is non-negotiable: `lair memory list/show/forget/export` CLI; injected memories appear in the routing explanation with provenance tag MEMORY; per-project off switch. The user owns and can read every byte.
- Interop watch-list: Mem0/Letta/MCP memory interfaces — consider exposing LAIR memory over MCP so other agents can use it, per the graphify MCP pattern.
- Requires RFC (user-facing behavior + privacy posture) and ADR (storage schema).

**Acceptance criteria.**
- [ ] Memories persist across server restarts and across two different clients pointed at the same project scope.
- [ ] Retrieval injection stays within the per-tier token budget; measured overhead <150ms on CPU.
- [ ] `lair memory` CLI: list, show, forget (single + wipe), export to JSON.
- [ ] Explanations tag injected memory; disabling memory yields byte-identical behavior to pre-I-18 LAIR.

---

## I-19 — LAIR Compact Models: quantum-inspired tensor-network compression (compress-once, run-everywhere)

**Status:** 💡 Proposed | **Priority:** High (strategic) | **Category:** Efficiency / Community / Differentiator | **Target:** 0.7+ (research track starts earlier)

**Description.** Per §1.10, tensor-network (MPO) compression — the quantum-inspired method behind Multiverse's CompactifAI — achieves up to ~93–95% size reduction with ~90%+ accuracy retention, and the compressed models run on plain CPUs. The method is published (arXiv 2401.14109; Minima 2026) and the math exists in open-source libraries (quimb, TensorLy). Multiverse monetizes it via cloud; **LAIR's mission-differentiated angle is bringing the results to local machines, free**: a community library of pre-compressed, healed, laptop-ready models that LAIR can recommend, download, and route to.

**Design notes.**
- Honest architecture (the healing retrain needs real GPUs): **compress-once, run-everywhere.** Compression + healing runs occasionally on capable hardware (maintainer GPU time, community members, donated compute); outputs are published as ordinary GGUF/safetensors artifacts anyone can run. LAIR itself never requires a GPU.
- Phase 1 (research): reproduce MPO decomposition on a small model (SmolLM3/Qwen 4B) with quimb; measure size/quality/speed; publish the pipeline as `scripts/compactify/`. RFC first.
- Phase 2 (catalog): `configs/compact_models/` registry of vetted compressed models with MEASURED benchmark scores (I-12/I-13 machinery) — tier-matched so `lair doctor` can recommend them.
- Phase 3 (community): accept community-contributed compressions with mandatory benchmark cards; provenance-tag everything.
- Framing discipline: always "quantum-inspired" (tensor networks on classical hardware). Real-QPU work (IBM Cayley adapters) stays on the watch-list only.
- Stacks with quantization (CompactifAI's own paper combines MPO + quant) — a compact model can additionally ship Q4/mixed-precision variants (I-17).

**Acceptance criteria.**
- [ ] RFC documenting the compression pipeline, quality bars (≥90% of source-model benchmark scores), and publication standards.
- [ ] One reproducible compression of a small open model with before/after benchmarks, runnable on a CPU_ONLY tier machine.
- [ ] Compact-model catalog format + loader; entries carry MEASURED provenance and tier fit.
- [ ] Documentation clearly distinguishes quantum-inspired vs quantum hardware.

---

# Part 3 — Implementation Sequence

Claude Code: implement in this order unless the user redirects. One item per session where feasible; each item follows RFC/ADR workflow when marked architectural.

*(All 20 entries below are now shipped — see "Implementation Status" near the top of this document for what landed, including the two honestly-scoped exceptions, I-16 and I-19.)*

**Wave 1 — Quick wins (v0.3):**
1. I-13 Provenance-tagged explanations (small, foundational — do first so later features emit tagged factors)
2. I-01 Savings dashboard
3. I-05 Single-slot scheduler (sticky bonus + TTL first; queueing later)
4. I-04 Complexity triage (rules phase)

**Wave 2 — Accessibility core (v0.3–0.4):**
5. I-02 `lair doctor` + tiered portfolios
6. I-03 Quantization-aware registry (ADR required — registry schema change)
7. I-14 `lair install`
8. I-10 Language-aware routing

**Wave 3 — Intelligence & scale (v0.4–0.5):**
9. I-07 Semantic cache (build the shared embedding layer here — I-08 and I-18 reuse it)
10. I-04 Complexity triage (model-assisted phase)
11. I-06 Hybrid cloud escalation (RFC + ADR required)
12. I-08 RAG-lite documents
13. I-09 Context compression
14. I-17 Advanced quantization intelligence (KV-cache fit model first; backend knobs as available)

**Wave 4 — Experience & community (v0.6):**
15. I-18 Persistent project memory (RFC + ADR required — the continuity differentiator; reuses Wave 3 embeddings)
16. I-11 Voice interface (expanded; integrates I-10 language routing + I-18 memory)
17. I-12 Community capability database
18. I-15 Battery awareness

**Wave 5 — Advanced efficiency & frontier (v0.6–0.7):**
19. I-16 Streaming-aware routing (pairs with Multi-Provider milestone; ADR for registry schema)
20. I-19 LAIR Compact Models — Phase 1 research (RFC), then catalog + community phases

Wave 5 items are frontier work: each begins with an RFC, and Phase-1 results decide how far to invest. They are also the plan's strongest long-term differentiators — "runs models your laptop shouldn't be able to run."

---

# Appendix A — Research Sources

- MoE/quantization on constrained hardware: "Running LLMs Locally in 2026" guides (Medium/Hoke; llm-stats.com; tensorrigs.com; carteakey.dev); LM Studio Low-VRAM Guide (lmsa.app, 2026)
- LM Studio features: lmstudio.ai/docs (TTL & Auto-Evict; Speculative Decoding; API server architecture)
- Routing research: RouteLLM (Ong et al., ICLR 2025); FrugalGPT (Chen et al.); HybridLLM (Ding et al., 2024); AutoMix (Aggarwal et al.); "Cluster, Route, Escalate" (arXiv 2606.27457, 2026); 2026 dynamic-routing survey
- Small models: daily.dev, BentoML, KDnuggets, sitepoint model roundups (2026) — Phi-4-mini, Gemma 3n, Qwen3.5-4B, SmolLM3, Llama 3.2 3B
- Voice stack: faster-whisper (CTranslate2); whisper.cpp; Kokoro-82M; OpenWakeWord; Piper archival note (Oct 2025); local voice assistant guides (dev.to, promptquorum, local-llm.net, 2026)
- Hybrid economics: daily.dev self-hosted AI case studies (2026)
- Layer streaming / SSD offload: AirLLM reality-check reviews (2026); ssd-llm (quantumnic, Apple Silicon mmap+prefetch); oLLM layer sharding; llama.cpp mmap discussion #19163; MLX out-of-core feature request #2878; tinycomputers.io partial-loading guide
- Advanced quantization: RateQuant (arXiv 2605.06675); PM-KVQ (OpenReview); KVmix (AAAI-26); adaptive on-device KV quant (arXiv 2604.04722); GPU INT8 KV compression (arXiv 2601.04719); MLX quantization comparisons (dynamic_quant/AWQ/GPTQ/DWQ); LLM Compressor 0.9.0 (Red Hat, Jan 2026)
- Agent memory: Mem0 "State of AI Agent Memory 2026"; vectorize.io & atlan.com framework comparisons (2026); Letta/MemGPT; Zep/Graphiti; Cognee; agentmemory (LongMemEval benchmarks; all-MiniLM-L6-v2 local embeddings); preuve.ai memory statistics 2026
- Tensor-network compression: CompactifAI (arXiv 2401.14109; ESANN 2025); Minima pipeline (arXiv 2602.01613); Multiverse announcements — $215M raise, Xeon-6 CPU demo (Jul 2025), HyperNova 60B (Feb 2026); quimb & TensorLy libraries; tensornetwork.org software list
- Quantum hardware watch-list: Cayley unitary adapters on IBM 156-qubit QPU (arXiv 2605.05914); QD-LLM quantum distillation (arXiv 2505.13205)
