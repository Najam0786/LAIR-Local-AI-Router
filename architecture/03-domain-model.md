# ARCH-03 — Domain Model

**Document ID:** ARCH-03

**Version:** 0.2.0-alpha

**Status:** Active

---

# Purpose

Describe the core business objects used throughout LAIR.

These objects form the shared language of the application.

---

# Core Domain Objects

```
AIModel
```

Represents an AI model known to LAIR.

Contains

• Provider

• Capability Profile

• Metadata

---

```
Capability
```

Represents an individual model capability.

Examples

• Reasoning

• Coding

• Vision

• Embedding

---

```
CapabilityProfile
```

Collection of capabilities describing a model.

---

```
CapabilityRequirement
```

Capabilities required to satisfy a user request.

---

```
RoutingDecision
```

Represents the outcome of the routing process.

Contains

• Selected Model

• Routing Score

• Reasons

---

```
Provider
```

Abstract interface implemented by every provider.

Examples

• LM Studio

• Ollama

• OpenAI

---

# Domain Relationships

```
Provider
    │
    ▼
AIModel
    │
    ▼
CapabilityProfile
    │
    ▼
Capability
```

```
Prompt
    │
    ▼
CapabilityRequirement
    │
    ▼
RoutingDecision
```

---

# Design Philosophy

Domain objects

• contain business data

• remain independent of FastAPI

• remain independent of providers

• are reusable throughout the application

---

# Future Domain Objects

Planned additions

• BenchmarkProfile

• ProviderHealth

• HardwareProfile

• RoutingHistory

• UserPreference

• DecisionLog

---

# Related Documents

ARCH-04

ARCH-05

ARCH-06

ARCH-07