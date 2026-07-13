# LAIR API Specification

**Project:** LAIR – Local AI Intelligence Router

**Status:** Draft

**Version:** 0.1.0

**Last Updated:** 2026-07-13

---

# Purpose

The LAIR API provides a unified interface for interacting with local and remote AI models.

Clients should never communicate directly with providers such as LM Studio or Ollama.

Instead, all requests pass through LAIR.

```
Application

↓

LAIR API

↓

Routing Engine

↓

Provider

↓

Model
```

This architecture enables intelligent routing, benchmarking, monitoring, and future orchestration without changing client applications.

---

# Design Principles

The API should be:

- RESTful
- Stateless
- Provider-agnostic
- Model-agnostic
- Versioned
- Fully documented
- Easy to extend

---

# Base URL

Local Development

```
http://localhost:8000
```

Future

```
https://lair.company.com/api/v1
```

---

# API Versioning

Current

```
v1
```

Future endpoints should follow:

```
/api/v1/
```

Examples

```
GET /api/v1/models

POST /api/v1/chat

GET /api/v1/providers
```

---

# Endpoint Categories

## Health

```
GET /health
```

Returns system status.

---

## Models

```
GET /models
```

Returns registered models.

Future:

```
GET /models/{id}

POST /models/reload

POST /models/benchmark
```

---

## Providers

Future

```
GET /providers

GET /providers/{provider}

POST /providers/reconnect
```

---

## Chat

Future

```
POST /chat
```

Executes intelligent routing and inference.

Example Request

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Explain transformers."
    }
  ]
}
```

---

## Routing

Future

```
POST /route
```

Returns the selected execution plan without running inference.

Example Response

```json
{
  "selected_model": "qwen3.6",
  "confidence": 97,
  "reason": [
    "Highest documentation score",
    "Fits context",
    "GPU available"
  ]
}
```

---

## Benchmarking

Future

```
GET /benchmarks

POST /benchmarks/run
```

---

## Registry

Future

```
GET /registry
```

Returns metadata for all registered models.

---

## Configuration

Future

```
GET /config

PATCH /config
```

Allows runtime configuration.

---

# Standard Request Format

Every inference request should follow one schema.

```json
{
  "messages": [],
  "temperature": 0.2,
  "max_tokens": 2048,
  "stream": true
}
```

LAIR converts this request to the provider-specific format.

---

# Standard Response Format

Every provider should return a normalized response.

```json
{
  "model": "qwen3.6",
  "provider": "lmstudio",
  "response": "...",
  "usage": {
    "prompt_tokens": 520,
    "completion_tokens": 842
  },
  "latency_ms": 820
}
```

---

# Error Format

Errors should be consistent across all endpoints.

```json
{
  "error": {
    "code": "ProviderUnavailable",
    "message": "LM Studio is not responding."
  }
}
```

Clients should never receive provider-specific errors.

---

# Authentication

Current

No authentication.

Future

- API Keys
- OAuth
- JWT
- Local Authentication

---

# Streaming

Streaming responses should use Server-Sent Events (SSE).

Clients should receive tokens as they are generated.

Example

```
data: Hello

data: world

data: !
```

---

# OpenAPI

Every endpoint should automatically appear in:

```
/docs
```

Swagger UI is the reference documentation during development.

---

# Performance Goals

Typical targets:

Health endpoint

< 5 ms

Model registry

< 50 ms

Routing decision

< 50 ms

Provider request overhead

< 10 ms

API latency should never dominate inference latency.

---

# Future Endpoints

Potential additions:

```
POST /embeddings

POST /vision

POST /reason

POST /summarize

POST /transcribe

POST /evaluate

POST /agents

POST /workflows

GET /metrics

GET /logs
```

---

# API Philosophy

The API should remain stable even as providers and models evolve.

Clients integrate with LAIR—not with individual AI models.

---

# Definition of Success

A client should be able to switch from:

LM Studio

↓

Ollama

↓

vLLM

↓

Cloud

without changing a single API call.

---

# Motto

> Stable APIs enable evolving intelligence.

---

## Open Questions

- Should GraphQL be supported?
- Should WebSockets complement SSE?
- Should plugins expose custom endpoints?
- Should every request receive a trace ID?