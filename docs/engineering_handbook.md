# LAIR Engineering Handbook

**Project:** LAIR – Local AI Intelligence Router

**Version:** 0.1.0-alpha

**Status:** Active

**Audience:** Contributors & Maintainers

---

# Purpose

The Engineering Handbook defines the development standards for LAIR.

It explains how software should be designed, implemented, tested, documented and reviewed.

Unlike architecture documents, this handbook focuses on engineering practices rather than system design.

---

# Engineering Philosophy

LAIR values:

- Simplicity over cleverness
- Readability over brevity
- Evidence over assumptions
- Modularity over coupling
- Consistency over preference

Every contribution should improve the maintainability of the project.

---

# Development Lifecycle

Every feature follows the same lifecycle.

```
Innovation Backlog

↓

Research

↓

Prototype

↓

RFC

↓

ADR

↓

Implementation

↓

Testing

↓

Benchmarking

↓

Documentation

↓

Review

↓

Release
```

No major feature should skip these stages.

---

# Project Structure

```
app/

benchmarks/

configs/

docs/

tests/

scripts/
```

Every component has one clear responsibility.

---

# Python Standards

Minimum Version

Python 3.13+

---

Style

PEP 8

---

Formatting

Black

---

Linting

Ruff

---

Type Checking

MyPy

---

Imports

Absolute imports whenever practical.

---

Naming Conventions

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

Private members

_prefix

---

# Type Hints

All public interfaces must use type hints.

Example

```python
def list_models() -> list[ModelInfo]:
    ...
```

Avoid untyped public functions.

---

# Documentation

Every public class and function should include:

- Purpose
- Parameters
- Return value
- Exceptions (if applicable)

Complex logic should explain *why*, not *what*.

---

# Logging

Logging should be:

- Structured
- Informative
- Non-redundant

Never log:

- Secrets
- API keys
- Personal data

---

# Configuration

Configuration belongs in:

```
.env

configs/
```

Never hard-code:

- URLs
- Ports
- API keys
- Model names
- File paths

---

# Error Handling

Errors should:

- Be explicit
- Include context
- Avoid silent failures
- Use custom exception types where appropriate

---

# Testing

Every feature should include:

- Unit tests
- Integration tests (where applicable)

Tests should be deterministic and isolated.

---

# Benchmarking

Performance-sensitive changes should be benchmarked.

Measure before optimizing.

Benchmark results should accompany significant performance improvements.

---

# Documentation Requirements

Every major feature should update:

- README (if user-facing)
- Relevant documentation
- ADR (if architectural)
- CHANGELOG (if released)

Documentation is part of the feature.

---

# Git Workflow

Recommended branch names:

```
feature/capability-engine

feature/routing-engine

feature/benchmark-runner

bugfix/provider-timeout

docs/api-update
```

---

# Commit Messages

Use Conventional Commits.

Examples:

```
feat: add capability engine

fix: handle provider timeout

docs: update routing specification

refactor: simplify model registry

test: add provider integration tests

perf: improve routing latency
```

---

# Code Review Checklist

Before merging:

- Code compiles
- Tests pass
- Type checking passes
- Linting passes
- Documentation updated
- No duplicated logic
- Logging reviewed
- Configuration externalized

---

# Definition of Done

A feature is complete when:

- Implementation finished
- Tests passing
- Benchmarks reviewed
- Documentation updated
- Code reviewed
- Ready for release

---

# Engineering Principles

Contributors should strive to:

- Prefer composition over inheritance
- Minimize dependencies
- Keep components loosely coupled
- Design for testability
- Avoid premature optimization
- Build incrementally

---

# LAIR Evolution Principle

New abstractions, layers, schemas, interfaces, and processes are introduced
only once multiple concrete use cases demonstrate a real need — not because
an idea sounds reasonable, sounds "almost free," or might matter someday.
The project prefers evolutionary design over speculative architecture.

Before adding any new class, layer, interface, data field, or process, ask:
**does this have a real, concrete second consumer today, or is it for a
hypothetical future case?** If the honest answer is "not yet," defer it and
note what would justify revisiting it — don't build it ahead of the need.

This has been applied consistently to code (rejecting a persisted Session
Manager, a separate ProviderAdapter layer, and a formal Application Service
class), to data (rejecting an `actual_model_used` field with no fallback
mechanism to justify it), to process (rejecting a formal "Dogfooding
Milestone" in favor of a plain log file), and to documentation itself
(rejecting a rigid observation template before enough real entries existed
to show what structure, if any, is actually needed).

---

# Long-Term Goal

The engineering process should remain predictable as LAIR grows from a personal project into a mature open-source platform.

---

# Motto

> Build with discipline. Measure with evidence. Improve continuously.

---

## Related Documents

- project_charter.md
- architecture.md
- principles.md
- benchmarking.md
- innovation_backlog.md