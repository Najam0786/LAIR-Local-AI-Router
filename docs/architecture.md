# LAIR Architecture

**Project:** LAIR – Local AI Intelligence Router

**Status:** Draft

**Version:** 0.1.0

**Last Updated:** 2026-07-13

---

# Overview

LAIR is an AI orchestration platform responsible for intelligently routing requests to the most appropriate AI model based on task requirements, model capabilities, benchmark results and available hardware.

LAIR sits between AI clients and AI providers.

Users interact with LAIR.

LAIR interacts with AI models.

---

# High-Level Architecture

```
                   ┌──────────────────────┐
                   │     VS Code          │
                   │     Continue         │
                   │      Cline           │
                   │      Roo             │
                   │      API             │
                   └──────────┬───────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │         LAIR API         │
                 └──────────┬───────────────┘
                            │
            ┌───────────────┼────────────────┐
            ▼               ▼                ▼
      Request Parser   Session Manager   Authentication
            │
            ▼
     Capability Extractor
            │
            ▼
      Routing Engine
            │
     ┌──────┴───────────┐
     ▼                  ▼
Benchmark Engine   Model Registry
     │                  │
     └──────┬───────────┘
            ▼
    Provider Manager
            │
     ┌──────┼──────────────┐
     ▼      ▼              ▼
 LM Studio Ollama     Cloud APIs
            │
            ▼
     AI Model Execution
            │
            ▼
     Response Processing
            │
            ▼
         Client
```

---

# Core Components

## API Layer

Responsibilities:

- Receive requests
- Validate requests
- Create sessions
- Return responses

The API layer contains no routing logic.

---

## Capability Extractor

The capability extractor determines what the user actually wants.

Examples:

Prompt:

> Explain transformers.

Capability:

Documentation

---

Prompt:

> Refactor this Python code.

Capability:

Coding

---

Prompt:

> Analyze this image.

Capability:

Vision

---

Prompt:

> Solve this mathematical proof.

Capability:

Reasoning

The routing engine consumes capabilities rather than raw prompts.

---

## Routing Engine

The routing engine is the brain of LAIR.

Inputs include:

- Requested capability
- Context length
- Available models
- Benchmark scores
- Hardware availability
- User preferences

Outputs:

- Selected model
- Confidence score
- Routing explanation

---

## Model Registry

The registry contains metadata for every available model.

Example:

- Provider
- Context window
- Vision support
- Coding capability
- Memory requirements
- Benchmark scores
- Preferred workloads

The registry contains metadata only.

It never performs inference.

---

## Provider Manager

The provider manager abstracts external inference engines.

Examples:

- LM Studio
- Ollama
- OpenAI
- Anthropic
- vLLM
- llama.cpp

Every provider exposes the same interface.

---

## Benchmark Engine

Responsible for measuring model performance.

Metrics include:

- Accuracy
- Speed
- Token throughput
- GPU utilization
- Memory usage
- Task-specific performance

Benchmark data influences routing decisions.

---

## Execution Engine

Responsibilities:

- Send prompt
- Stream tokens
- Retry on failure
- Handle timeouts
- Return responses

Execution is isolated from routing.

---

## Logging System

Everything should be logged.

Examples:

- Request ID
- Selected model
- Routing reason
- Tokens
- Execution time
- Errors

Logs become valuable benchmark data.

---

# Request Lifecycle

A typical request follows these steps.

```
Client

↓

API

↓

Capability Extraction

↓

Routing Engine

↓

Registry Lookup

↓

Benchmark Evaluation

↓

Provider Selection

↓

Model Execution

↓

Response

↓

Logging
```

---

# Data Flow

The registry provides knowledge.

The benchmark engine provides measurements.

The routing engine makes decisions.

Providers execute requests.

The execution engine returns results.

Each component has a single responsibility.

---

# Design Goals

The architecture should satisfy:

- High cohesion
- Low coupling
- Provider independence
- Model independence
- Explainability
- Extensibility
- Testability

---

# Future Components

Future versions of LAIR may include:

## Learning Engine

Learns from historical executions.

---

## Hardware Profiler

Continuously measures:

- GPU memory
- RAM
- CPU utilization
- Temperature
- Power consumption

---

## Ensemble Engine

Routes one request to multiple models simultaneously.

Example:

Reasoning:

DeepSeek

Coding:

Qwen

Documentation:

Gemma

Results are combined into a final answer.

---

## RAG Engine

Supports:

- Local documents
- Vector databases
- Knowledge graphs
- Semantic search

---

## Workflow Engine

Coordinates multiple AI tasks.

Example:

Analyze →

Reason →

Code →

Review →

Document

---

# Architectural Principles

Every subsystem should:

- Have one responsibility
- Be independently testable
- Be replaceable
- Expose clear interfaces
- Avoid direct dependencies

---

# Definition of Success

The architecture succeeds when:

- Adding a provider requires minimal code changes.
- Adding a model requires only registry updates.
- Routing algorithms can evolve independently.
- Execution providers remain interchangeable.
- Future AI capabilities integrate without redesigning the system.

---

# Motto

> Modular architecture enables intelligent evolution.

---

## Open Questions

- Should routing become event-driven?
- Should providers execute concurrently?
- Should benchmark updates occur asynchronously?
- Should multiple routing strategies coexist?