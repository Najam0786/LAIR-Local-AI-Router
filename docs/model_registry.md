# Model Registry

**Project:** LAIR – Local AI Intelligence Router

**Status:** Draft

**Version:** 0.1.0

**Last Updated:** 2026-07-13

---

# Purpose

The Model Registry is the knowledge base of LAIR.

It stores metadata describing every available AI model without performing inference.

The routing engine relies on this metadata to make intelligent model selection decisions.

The registry never executes models.

It only answers questions about them.

---

# Why a Registry Exists

Most AI systems identify models only by name.

Example:

```
if model == "qwen":
```

This approach does not scale.

Instead, LAIR identifies models by their capabilities.

Example:

```
Supports Coding

Supports Vision

Supports Reasoning

Supports Long Context
```

Routing decisions are therefore capability-driven rather than model-driven.

---

# Registry Responsibilities

The registry is responsible for:

- Discovering available models
- Storing metadata
- Tracking capabilities
- Recording benchmark scores
- Recording hardware requirements
- Reporting provider information
- Exposing searchable metadata

The registry never performs routing.

The registry never performs inference.

---

# Model Metadata

Every model should expose the following information.

## Identity

- Model ID
- Display Name
- Family
- Version
- Provider

Example

```
Model

Qwen3.6 35B A3B

Family

Qwen

Provider

LM Studio
```

---

## Capabilities

Capabilities describe what the model can do.

Examples include:

- Coding
- Documentation
- Reasoning
- Vision
- Mathematics
- Tool Calling
- Embeddings
- Function Calling
- Translation
- Summarization

Capabilities should remain independent of model names.

---

## Context

Examples:

- Context Window
- Maximum Output Tokens
- Prompt Caching
- Streaming Support

---

## Hardware Profile

Examples:

- Recommended RAM
- Recommended VRAM
- CPU Compatible
- GPU Compatible
- Quantization
- Memory Footprint

---

## Performance

Performance data should include:

- Average Latency
- Tokens Per Second
- Prompt Processing Speed
- Completion Speed
- GPU Utilization
- CPU Utilization

These values should come from benchmarks rather than documentation.

---

## Benchmark Scores

Each capability receives an independent score.

Example:

| Capability | Score |
|------------|------:|
| Coding | 96 |
| Reasoning | 90 |
| Vision | 82 |
| Documentation | 95 |
| Long Context | 97 |

Overall scores should not replace capability scores.

---

# Example Registry Entry

```yaml
id: qwen/qwen3.6-35b-a3b

provider: lmstudio

family: qwen

parameters: 35B

context_window: 262144

vision: false

coding: 96

reasoning: 91

documentation: 94

long_context: 97

tool_calling: true

embeddings: false

recommended_ram: 32GB

recommended_gpu: Intel Arc A370M

benchmark_version: 1.0
```

---

# Registry Operations

The registry should support:

- Register Model
- Remove Model
- Update Metadata
- List Models
- Search by Capability
- Search by Provider
- Search by Context
- Search by Benchmark Score

---

# Discovery

Providers should automatically populate the registry.

Example:

LM Studio

↓

GET /v1/models

↓

Registry Update

↓

Available for Routing

No manual registration should be required.

---

# Registry Validation

Every registered model should be validated.

Checks include:

- Unique Model ID
- Provider Exists
- Context Window Valid
- Capability Scores Present
- Metadata Complete

Invalid models should not enter the registry.

---

# Future Enhancements

Future versions may include:

- Automatic capability detection
- Benchmark synchronization
- Online model updates
- Community benchmark sharing
- Hardware recommendation engine
- Version compatibility tracking

---

# Relationship to Other Components

Registry responsibilities:

- Stores knowledge

Routing Engine responsibilities:

- Makes decisions

Provider responsibilities:

- Executes inference

Benchmark Engine responsibilities:

- Produces measurements

Keeping these responsibilities separate improves maintainability.

---

# Definition of Success

The registry succeeds when:

- Every model is described consistently.
- Models are searchable by capability.
- Routing never depends on model names.
- New providers integrate automatically.
- Benchmark information remains current.

---

# Motto

> Models are identified by what they can do, not by what they are called.

---

## Open Questions

- Should capability scores be manually assigned, benchmark-derived, or learned automatically?
- Should registry metadata be stored in YAML, JSON, or a database?
- How should multiple benchmark versions be managed?