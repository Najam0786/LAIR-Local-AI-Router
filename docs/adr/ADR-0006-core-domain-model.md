# ADR-0006 — Core Domain Model

**Status:** Accepted

**Date:** 2026-07-14

---

# Context

LAIR's architecture is evolving from a simple router into a decision engine for AI workloads.

Several core nouns have been discussed informally, with competing names:

- Request vs Task
- RoutingDecision vs DecisionRecord
- ExecutionPlan vs ExecutionStrategy

Implementing future phases against inconsistent ad hoc names risks rework once Benchmark Engine, Learning Engine and the Execution Planner depend on these shapes.

---

# Decision

LAIR adopts the following ubiquitous language. Every future ADR, module and API builds on these terms.

- **Task** — the domain representation of work to perform, independent of transport. HTTP, CLI, VS Code, SDK and queue adapters all translate into the same Task.
- **Intent** — the classified purpose of a Task (coding, summarization, reasoning, vision, translation, ...).
- **Objective** — the optimization target for a Task (lowest latency, highest quality, lowest cost, lowest VRAM, highest reasoning).
- **Constraint** — a hard limit a solution must satisfy (context length, memory ceiling, local-only).
- **Requirement** — a capability implied by Intent, Objective and Constraint. Derived, not user-authored, but versioned and inspectable — never discarded because it is derived.
- **CapabilityProfile** — the declared or measured capabilities of a model.
- **CapabilityEvidence** — provenance for a capability claim: source, confidence, timestamp, benchmark, provider, version.
- **ResourceProfile** — the cost of running a model: VRAM, RAM, expected latency.
- **ProviderProfile** — the health, priority and reachability of a provider.
- **KnowledgeBase** — the queryable store of benchmarks, capability evidence, hardware profiles, provider statistics and historical decisions. Read-only from the Decision Engine; written by the Benchmark Engine, Learning Engine and provider health monitors.
- **RoutingPolicy** — the single source of scoring weights and priorities. Read by every scorer; written by the Learning Engine; exposed through the API.
- **DecisionProblem** — a Task combined with its Objective, Constraints, Requirements and candidate set. What the Decision Engine reasons over.
- **Decision Engine** — the component that resolves a DecisionProblem into an ExecutionStrategy, using RoutingPolicy and KnowledgeBase. Its decision space includes single-model, workflow, reject and clarify — not only model selection.
- **DecisionRecord** — the immutable, auditable trace of a decision: the DecisionProblem considered, every candidate's scores, the RoutingPolicy version, the KnowledgeBase snapshot version, and the chosen ExecutionStrategy.
- **Explanation** — a human-readable projection of a DecisionRecord. Generated from the record; never an independent source of truth.
- **ExecutionStrategy** — the chosen approach for fulfilling a Task: single-model, chain, ensemble-vote, reject or clarify.
- **ExecutionPlan** — the concrete, resolved sequence of ExecutionSteps that instantiates an ExecutionStrategy for one Task.
- **ExecutionStep** — one unit of work in an ExecutionPlan: a role, a model, a provider, and its dependencies.
- **Provider** — an inference backend (LM Studio, Ollama, vLLM, OpenAI-compatible, ...) behind the BaseProvider contract.

---

# Alternatives Considered

## Let Vocabulary Emerge Per Phase

Pros

- No upfront overhead

Cons

- High risk of inconsistent or renamed core objects once later phases already depend on earlier shapes
- Expensive rework, particularly for objects other subsystems read from (DecisionRecord, RoutingPolicy)

## Defer Naming Until Each Phase Begins

Cons

- Contradicts LAIR's architecture-first workflow
- Several objects are referenced by multiple future phases and need to be agreed once, not redefined per phase

---

# Consequences

Benefits

- Shared vocabulary across code, docs and future ADRs
- Reduces risk of redesigning core nouns after data or consumers depend on them
- Later ADRs reference these terms instead of redefining them

Trade-offs

- Introduces named concepts (DecisionProblem, ExecutionStrategy, KnowledgeBase, ...) ahead of their implementation
- Must be tracked as intentional scaffolding in documentation, not code, and revisited if implementation reveals a term does not fit

---

# Decision Summary

The language of LAIR is defined before the code that implements it, so every future ADR and roadmap phase builds on the same nouns.
