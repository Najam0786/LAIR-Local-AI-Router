# ADR-0004 — Capability-Based Routing

**Status:** Accepted

**Date:** 2026-07-13

---

# Context

Most AI applications route requests using hard-coded model names.

This makes routing fragile as new models appear.

---

# Decision

LAIR routes requests using model capabilities instead of model names.

Examples:

- Coding
- Reasoning
- Vision
- Documentation
- Long Context

---

# Consequences

Benefits

- Model independence
- Future compatibility
- Easier benchmarking
- Simpler maintenance

---

# Decision Summary

Models are selected because of what they can do, not because of what they are called.