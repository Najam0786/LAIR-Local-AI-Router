# LAIR Development Roadmap

## Current Status

Version

0.3.0-alpha

Status

Capability Engine and Intelligent Routing phases complete. All 20 entries
of `docs/INNOVATION_PLAN_2026.md`'s Implementation Sequence (Waves 1-5:
provenance-tagged explanations, savings dashboard, TTL scheduling,
complexity triage, hardware-aware onboarding, quantization-aware
registry, one-command IDE install, language-aware routing, response
cache, hybrid cloud escalation, RAG-lite documents, context compression,
advanced quantization intelligence, persistent project memory, voice
interface, community capability database, battery awareness,
streaming-aware routing infrastructure, and Phase 1a of tensor-network
compact models) have shipped as of 2026-07-25 -- see that document's own
"Implementation Status" section for exactly what landed, including two
items (streaming-aware routing execution, real-model compact-model
compression) that shipped their infrastructure honestly-scoped, with
execution named as follow-up work tied to the Multi-Provider milestone.

---

# Phase 0

Architecture

✅ Complete

- Product Vision
- Architecture
- Registry
- Providers
- ADR
- RFC
- Research
- Documentation
- Engineering Standards

---

# Phase 1

Capability Engine

Target Version

0.2

Objectives

- Capability extraction
- Capability profiles
- Capability database
- Capability scoring

Status

✅ Complete (capability database persistence remains an open question --
see `docs/INNOVATION_PLAN_2026.md` Implementation Sequence item 2;
profiles today are cheaply re-resolved from provider metadata each
request, which may turn out to be sufficient)

---

# Phase 2

Intelligent Routing

Target Version

0.3

Objectives

- Routing engine
- Explainable routing
- Confidence scoring
- Decision logging

Status

✅ Complete (explainability now includes per-factor provenance tags --
MEASURED / COMMUNITY / DECLARED / HEURISTIC / MEMORY -- via I-13)

---

# Phase 3

Benchmark Engine

Target Version

0.4

Objectives

- Benchmark runner
- Performance metrics
- Hardware profiling
- Routing validation

Status

🟡 In Progress (benchmark runner, performance metrics, and hardware
profiling shipped, plus community-contributed benchmark fallback (I-12)
and advanced quantization/KV-cache intelligence (I-17); Router Decision
Accuracy measurement -- comparing persisted decisions against
benchmark-optimal picks -- not yet built, see `docs/innovation_backlog.md`
"Router Decision Accuracy")

---

# Phase 4

Multi-Provider

Target Version

0.5

Objectives

- Ollama
- vLLM
- OpenAI-compatible
- Failover
- Load balancing

Status

🟡 Not started for local backends (Ollama/vLLM). An OpenAI-compatible
*cloud* provider shipped early, gated behind hybrid cloud escalation
(I-06, RFC-0001, ADR-0018) -- off by default, a budget-capped exception
for genuinely hard requests, not a general multi-backend abstraction.
I-16's streaming-aware routing (ADR-0021) also depends on this phase:
its registry schema and routing logic are ready, but the actual
SSD-streaming execution path needs a llama.cpp-direct provider this
phase would introduce.

---

# Phase 5

Learning Engine

Target Version

0.6

Objectives

- Adaptive routing
- Feedback learning
- Decision optimization

---

# Phase 6

Developer Experience

Target Version

0.8

Objectives

- VS Code extension
- CLI
- Dashboard
- Visual routing explorer

---

# Phase 7

Enterprise

Target Version

0.9

Objectives

- Authentication
- RBAC
- Monitoring
- Audit logs

---

# Phase 8

Public Release

Target Version

1.0

Objectives

- Stable API
- Documentation complete
- Comprehensive benchmarks
- CI/CD
- Plugin SDK

---

# Long-Term Vision (2.x)

- Distributed LAIR
- Multi-Agent Orchestration
- Federated AI
- Decision Graph
- Self-Learning Router
- Hardware Scheduler