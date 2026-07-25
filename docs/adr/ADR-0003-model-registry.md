# ADR-0003 — Model Registry

**Status:** Accepted

**Date:** 2026-07-13

---

# Context

AI models differ in capabilities, context windows, hardware requirements and performance.

Using only model names does not provide enough information for intelligent routing.

---

# Decision

Introduce a centralized Model Registry that stores metadata for every available model.

The registry acts as the single source of truth for model capabilities.

---

# Alternatives Considered

## Hard-coded Model Lists

Pros

- Easy to implement

Cons

- Difficult to maintain
- Poor scalability
- Not extensible

---

# Consequences

Benefits

- Capability-based routing
- Automatic discovery
- Provider independence
- Centralized metadata

---

# Decision Summary

The Model Registry stores knowledge.

It never performs inference.