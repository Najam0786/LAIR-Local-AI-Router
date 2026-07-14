# ARCH-02 — Project Structure

**Document ID:** ARCH-02

**Version:** 0.2.0-alpha

**Status:** Active

---

# Purpose

Describe the physical layout of the LAIR repository and define the
responsibilities of each package.

---

# Repository Structure

```
LAIR
│
├── app/
├── architecture/
├── docs/
├── tests/
├── CHANGELOG.md
├── ROADMAP.md
├── README.md
├── pyproject.toml
└── .env.example
```

---

# Application Structure

```
app
│
├── api
├── capabilities
├── core
├── models
├── providers
├── registry
├── routing
├── schemas
└── services
```

---

# Package Responsibilities

## api

REST API endpoints.

No business logic.

---

## routing

Core routing logic.

Converts prompts into routing decisions.

---

## capabilities

Represents model capabilities and matching algorithms.

---

## providers

Interfaces with external AI providers.

---

## registry

Maintains provider and model registries.

---

## models

Domain models representing AI concepts.

---

## schemas

Public API contracts.

---

## core

Configuration and shared infrastructure.

---

# Dependency Rules

Allowed

```
API
 ↓
Routing
 ↓
Capabilities
 ↓
Providers
```

Not Allowed

```
Provider
 ↓
API
```

```
Schemas
 ↓
Routing
```

Business logic should never depend on API contracts.

---

# Design Goals

• Low coupling

• High cohesion

• Easy testing

• Provider independence

• Clear ownership

---

# Related Documents

ARCH-01

ARCH-03

ARCH-04