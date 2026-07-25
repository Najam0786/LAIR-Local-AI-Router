# Provider Architecture

**Project:** LAIR – Local AI Intelligence Router

**Status:** Draft

**Version:** 0.1.0

**Last Updated:** 2026-07-13

---

# Purpose

Providers are responsible for communicating with AI inference backends.

A provider translates LAIR's internal request format into the API expected by an inference engine and converts the response back into LAIR's standard format.

Providers never perform routing.

Providers never benchmark models.

Providers never make decisions.

They only execute requests.

---

# Design Goals

Every provider should:

- Follow a common interface.
- Be independently testable.
- Be easily replaceable.
- Support streaming responses.
- Report errors consistently.
- Expose available models.
- Hide provider-specific implementation details.

---

# Supported Providers

Current:

- LM Studio

Planned:

- Ollama
- llama.cpp
- vLLM
- OpenAI
- Anthropic
- Google Gemini
- Azure OpenAI
- Hugging Face TGI

Future providers should require minimal code changes.

---

# Provider Responsibilities

A provider is responsible for:

- Listing available models
- Executing inference
- Streaming responses
- Handling authentication
- Reporting provider status
- Normalizing responses

---

# Standard Provider Interface

Every provider should implement the following operations.

```
connect()

disconnect()

health()

list_models()

chat()

completion()

embeddings()

stream()

cancel()
```

Not every provider must support every feature.

Unsupported features should return a standard capability response.

---

# Standard Request

Internally LAIR should use one request format.

Example

```yaml
provider: lmstudio

model: qwen3.6

messages:

- role: user
  content: Explain transformers.

temperature: 0.2

max_tokens: 2048

stream: true
```

Providers convert this request into their own API format.

---

# Standard Response

Every provider should return a normalized response.

Example

```yaml
provider: lmstudio

model: qwen3.6

completion:

Transformers...

usage:

prompt_tokens: 812

completion_tokens: 621

latency_ms: 820
```

---

# Error Handling

Provider errors should never leak provider-specific details.

Example

Instead of:

```
HTTP 503
```

Return:

```yaml
ProviderUnavailable
```

LAIR handles translation into user-friendly messages.

---

# Streaming

Streaming should follow a unified interface regardless of provider.

Consumers should never know whether tokens come from:

- LM Studio
- Ollama
- OpenAI
- Anthropic

Streaming should behave identically.

---

# Provider Discovery

Providers should register automatically.

Example

```
LM Studio

↓

Provider Manager

↓

Registry

↓

Available
```

---

# Health Monitoring

Providers should periodically report:

- Online status
- Latency
- Supported models
- API version
- Current load

Routing decisions may use this information.

---

# Security

Providers should never expose:

- API keys
- Authentication tokens
- Internal endpoints
- Sensitive configuration

Secrets belong in configuration management.

---

# Future Enhancements

Future versions may support:

- Load balancing
- Failover
- Provider clusters
- Distributed inference
- Remote execution
- Cost-aware routing

---

# Definition of Success

A new provider should be integrated by implementing one interface and registering it.

No routing code should require modification.

---

# Motto

> Providers execute. LAIR decides.

---

## Open Questions

- Should providers expose capability metadata?
- Should providers report hardware metrics?
- Should providers support automatic reconnection?