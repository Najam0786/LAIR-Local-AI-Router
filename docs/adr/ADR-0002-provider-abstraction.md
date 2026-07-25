# ADR-0002 — Provider Abstraction

**Status:** Accepted

**Date:** 2026-07-13

---

# Context

Different inference engines expose different APIs.

Examples include:

- LM Studio
- Ollama
- OpenAI
- Anthropic
- vLLM

Direct integration with each provider throughout the codebase would tightly couple LAIR to specific implementations.

---

# Decision

LAIR introduces a Provider Interface.

Every inference backend must implement the same contract.

Routing, benchmarking and execution remain independent of provider-specific APIs.

---

# Alternatives Considered

## Direct Integration

Pros

- Simple initial implementation

Cons

- Difficult maintenance
- Vendor lock-in
- Duplicate logic

---

# Consequences

Benefits

- Provider independence
- Easier testing
- Cleaner architecture
- Future extensibility

Trade-offs

- Additional abstraction layer

---

# Decision Summary

Provider-specific logic belongs inside providers.

Business logic must never depend on provider implementations.