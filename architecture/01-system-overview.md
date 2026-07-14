# ARCH-01 — System Overview

**Document ID:** ARCH-01

**Version:** 0.2.0-alpha

**Status:** Active

**Last Updated:** 2026-07-14

---

# Purpose

This document provides a high-level overview of the LAIR architecture,
its objectives, guiding principles, and the major software components.

It serves as the entry point to the Architecture Handbook.

---

# What is LAIR?

LAIR (Local AI Intelligence Router) is an intelligent routing platform
designed to select the most suitable AI model for a given task.

Instead of binding applications to a single model, LAIR evaluates the
capabilities of available models and automatically selects the most
appropriate one.

The long-term goal is to become a provider-independent AI decision engine.

---

# Vision

Build a unified intelligence layer capable of routing requests across
multiple AI providers using transparent, explainable, and data-driven
decision making.

---

# Core Principles

• Provider Independent

• Explainable Decisions

• Capability-Based Routing

• Extensible Architecture

• Clean Separation of Responsibilities

• API First

---

# High-Level Architecture

```
                Client
                   │
                   ▼
             FastAPI API Layer
                   │
                   ▼
             Routing Engine
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
Request Analyzer       Model Selector
       │                       │
       ▼                       ▼
 Capability Engine      Routing Decision
       │
       ▼
 Provider Registry
       │
       ▼
 AI Providers
       │
       ▼
 LM Studio / Ollama / OpenAI / vLLM
```

---

# Architectural Layers

Presentation Layer

• FastAPI

• Schemas

• REST API

Routing Layer

• Request Analyzer

• Routing Engine

• Model Selector

Capability Layer

• Capability Profiles

• Capability Resolver

• Capability Engine

Provider Layer

• Provider Registry

• Provider Implementations

Infrastructure Layer

• Configuration

• Logging

• HTTP Clients

---

# Current Features

Version 0.2.0-alpha includes

• Capability-aware routing

• Provider registry

• Model registry

• LM Studio integration

• Routing engine

• Explainable routing foundation

---

# Out of Scope

Current releases do not yet include

• Benchmark-based ranking

• Multi-provider failover

• Adaptive learning

• Distributed routing

---

# Related Documents

ARCH-02 — Project Structure

ARCH-03 — Domain Model

ARCH-04 — Provider Architecture

ARCH-05 — Capability Engine

ARCH-06 — Routing Engine