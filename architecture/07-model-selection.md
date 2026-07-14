# ARCH-07 — Model Selection

**Document ID:** ARCH-07

**Version:** 0.2.0-alpha

**Status:** Active

---

# Purpose

Select the most appropriate model from all compatible candidates.

---

# Selection Pipeline

Compatible Models

↓

Scoring

↓

Ranking

↓

Routing Decision

---

# Current Scoring

Current implementation considers

• Streaming support

• Context window

• Capability count

---

# Future Scoring

Planned factors

• Benchmark score

• Latency

• Memory usage

• Hardware profile

• User preferences

• Historical performance

• Provider priority

---

# Explainability

Every routing decision should explain

Why this model?

Why not another?

What capabilities matched?

How was the score calculated?

---

# Design Principles

Selection should be

• Transparent

• Deterministic

• Configurable

• Explainable

---

# Example

Prompt

↓

Candidate Models

↓

DeepSeek

Score 87

↓

Routing Decision

Reasons

• Supports reasoning

• Supports coding

• Highest routing score

---

# Future Enhancements

• Weighted scoring

• Machine learning ranking

• Benchmark integration

• Adaptive scoring

• Explainability reports

---

# Related Documents

ARCH-06

ARCH-08

ARCH-13