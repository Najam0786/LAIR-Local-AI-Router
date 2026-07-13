# ADR-0001 — Local First Architecture

**Status:** Accepted

**Date:** 2026-07-13

---

# Context

Many AI development tools depend heavily on cloud APIs.

This introduces:

- Cost
- Latency
- Privacy concerns
- Vendor lock-in
- Internet dependency

---

# Decision

LAIR adopts a Local First architecture.

The routing engine assumes that locally available models are preferred whenever they satisfy the task requirements.

Cloud providers remain optional extensions.

---

# Alternatives Considered

## Cloud First

Pros

- Larger models
- Unlimited scaling

Cons

- Cost
- Latency
- Privacy

---

## Hybrid

Pros

- Flexible

Cons

- Increased routing complexity

---

# Consequences

Benefits

- Privacy
- Offline operation
- Predictable cost
- Low latency
- Full hardware utilization

Trade-offs

- Hardware limitations
- Local model management

---

# Decision Summary

LAIR prioritizes local execution and treats cloud inference as an optional capability rather than the default.