# ARCH-04 — Provider Architecture

**Document ID:** ARCH-04

**Version:** 0.2.0-alpha

**Status:** Active

---

# Purpose

This document describes the provider abstraction layer.

The provider layer isolates LAIR from vendor-specific APIs,
allowing new providers to be added without changing the routing engine.

---

# Design Goals

• Provider independence

• Unified interface

• Easy extensibility

• Minimal coupling

• Consistent model discovery

---

# Architecture

                Routing Engine
                       │
                       ▼
               Provider Registry
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
 LM Studio Provider            Future Providers
        │
        ▼
 LM Studio API

---

# Provider Interface

Every provider must implement:

• list_models()

• health_check()

Future versions may include:

• generate()

• embeddings()

• chat()

• stream()

---

# Provider Registry

Responsibilities

• Register providers

• Discover providers

• Aggregate models

• Health monitoring

---

# Current Providers

Supported

• LM Studio

Planned

• Ollama

• OpenAI

• Anthropic

• vLLM

---

# Design Principles

Providers should never

• contain routing logic

• contain capability matching

• contain business rules

Providers are adapters.

---

# Data Flow

Client

↓

Routing Engine

↓

Provider Registry

↓

Provider

↓

External API

↓

Provider Registry

↓

Routing Engine

---

# Future Enhancements

• Provider plugins

• Dynamic provider loading

• Health monitoring

• Provider priorities

• Automatic failover

---

# Related Documents

ARCH-05

ARCH-06

ARCH-07