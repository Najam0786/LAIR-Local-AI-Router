# Routing Engine

**Project:** LAIR – Local AI Intelligence Router

**Status:** Draft

**Version:** 0.1.0

**Last Updated:** 2026-07-13

---

# Purpose

The Routing Engine is the decision-making core of LAIR.

Its responsibility is to analyze incoming requests, evaluate all available models, and select the optimal execution strategy.

The routing engine never performs inference.

It only decides who should perform inference.

---

# Philosophy

Users should never choose models.

Users describe problems.

LAIR determines the best execution strategy.

Routing decisions should always be:

- Explainable
- Repeatable
- Benchmark-driven
- Hardware-aware
- Capability-based

---

# Inputs

The routing engine considers multiple sources of information.

## User Request

Example:

> Explain attention mechanisms.

---

## Capability Extraction

Example:

Documentation

---

## Registry Metadata

Examples:

- Context Window
- Vision Support
- Coding Score
- Reasoning Score
- Documentation Score

---

## Benchmark Database

Examples:

- Accuracy
- Speed
- GPU Usage
- Reliability

---

## Hardware Profile

Examples:

- Available RAM
- Available GPU Memory
- CPU Utilization
- Active Models

---

## User Preferences

Optional preferences include:

- Prefer Local
- Prefer Fast
- Prefer Accurate
- Prefer Lowest RAM
- Prefer Open Source

---

# Routing Pipeline

Every request follows the same pipeline.

```
Incoming Request

↓

Capability Extraction

↓

Candidate Discovery

↓

Capability Filtering

↓

Hardware Validation

↓

Benchmark Scoring

↓

Final Ranking

↓

Model Selection

↓

Execution
```

---

# Candidate Discovery

The router first discovers every model capable of performing the requested task.

Example

Request:

> Refactor this Python code.

Candidates:

- Qwen3.6
- DeepSeek
- Gemma

Vision-only models are excluded.

---

# Capability Filtering

Each candidate receives a capability score.

Example:

| Model | Coding |
|--------|--------|
| Qwen | 96 |
| DeepSeek | 90 |
| Gemma | 87 |

Models below a configurable threshold are removed.

---

# Context Validation

The router verifies that the model can process the required context.

Example

Prompt:

190k tokens

Available:

Qwen

262k

Gemma

131k

DeepSeek

32k

Only Qwen remains.

---

# Hardware Validation

The router verifies:

- Available RAM
- GPU Memory
- Active Load
- Estimated Inference Cost

Example

DeepSeek requires 26GB RAM.

Available:

18GB

DeepSeek becomes unavailable.

---

# Benchmark Evaluation

Remaining candidates are ranked using benchmark scores.

Example:

| Model | Benchmark |
|--------|----------:|
| Qwen | 95 |
| Gemma | 92 |
| DeepSeek | 90 |

---

# Composite Scoring

Routing should not rely on a single metric.

Instead:

```
Final Score

=

Capability Score

+

Benchmark Score

+

Hardware Score

+

Availability Score

+

User Preference Score
```

Every component contributes to the final decision.

---

# Explainability

Every routing decision should produce an explanation.

Example:

Selected:

Qwen3.6

Reason:

Highest coding benchmark.

Fits context window.

GPU available.

Fastest estimated execution.

Confidence:

97%

---

# Failure Strategy

If no model satisfies all requirements:

Attempt:

Second-ranked model

↓

Lower capability threshold

↓

Cloud provider (optional)

↓

Return routing failure

Routing should fail gracefully.

---

# Multi-Model Routing

Future versions may execute multiple models simultaneously.

Example

Prompt:

Review this Python application.

Pipeline:

DeepSeek

↓

Reasoning

↓

Qwen

↓

Code Improvement

↓

Gemma

↓

Documentation

↓

Combined Response

---

# Learning-Based Routing

Future routing may adapt automatically.

Learning signals include:

- Benchmark improvements
- User feedback
- Historical success
- Execution latency
- Hardware utilization

The router should become increasingly intelligent.

---

# Routing Modes

Future modes may include:

## Fastest

Lowest latency.

---

## Highest Accuracy

Best benchmark score.

---

## Lowest Memory

Minimum hardware usage.

---

## Hybrid

Balanced optimization.

---

## Ensemble

Multiple models.

---

# Decision Record

Every routing decision should generate structured metadata.

Example

```yaml
request_id: 72819

selected_model: qwen3.6

reason:

- Highest Coding Score
- Hardware Available
- Fits Context
- Benchmark Rank #1

confidence: 97%

execution_mode: Local
```

This metadata supports observability and debugging.

---

# Performance Goals

Typical routing decisions should complete in:

< 50 ms

The routing engine should never become the performance bottleneck.

---

# Definition of Success

A successful router:

- Makes explainable decisions.
- Selects the best available model.
- Adapts to changing hardware.
- Learns from benchmark data.
- Avoids hard-coded rules.
- Improves over time.

---

# Motto

> Intelligence is choosing the best path, not following the first one.

---

## Open Questions

- Should routing weights be user configurable?
- Should confidence scores be probabilistic?
- Should routing support A/B testing?
- Should historical execution influence future decisions?