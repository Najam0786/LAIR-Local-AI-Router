# ARCH-09 — Configuration

**Document ID:** ARCH-09

**Version:** 0.2.0-alpha

**Status:** Active

---

# Purpose

Describe how LAIR is configured.

Configuration is centralized through Pydantic Settings and environment
variables.

---

# Configuration Sources

Priority

Environment Variables

↓

.env

↓

Default Values

---

# Core Settings

Application

• Name

• Version

• Debug

API

• Host

• Port

Providers

• Default Provider

• LM Studio URL

• Ollama URL

Models

• Default Model

Routing

• Capability Routing

• Explainability

• Benchmarks

---

# Design Principles

• Centralized

• Strongly typed

• Environment driven

• Easy deployment

---

# Configuration Files

settings.py

Application defaults

.env.example

Configuration template

.env

Local configuration

---

# Future Enhancements

• Provider-specific configuration

• Runtime configuration reload

• Configuration validation

---

# Related Documents

ARCH-04

ARCH-08