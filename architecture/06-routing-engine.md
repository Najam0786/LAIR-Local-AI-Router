# ARCH-06 — Routing Engine

**Document ID:** ARCH-06

**Version:** 0.2.0-alpha

**Status:** Active

---

# Purpose

The Routing Engine coordinates the complete routing workflow.

It does not score models.

It does not communicate with providers.

Its responsibility is orchestration.

---

# Architecture

Prompt

↓

Request Analyzer

↓

Capability Requirements

↓

Capability Engine

↓

Candidate Models

↓

Model Selector

↓

Routing Decision

---

# Responsibilities

• Analyze prompts

• Build requirements

• Filter models

• Delegate ranking

• Return routing decision

---

# Request Analyzer

Converts user prompts into capability requirements.

Example

"Write Python code"

↓

Coding

↓

Reasoning

---

# Candidate Selection

Capability Engine returns every compatible model.

No ranking occurs here.

---

# Routing Decision

Contains

• Selected model

• Score

• Reasons

---

# Design Principles

Routing Engine

• orchestrates

• delegates

• remains stateless

• contains no provider logic

---

# Future Enhancements

• Decision logging

• Multi-stage routing

• Retry policies

• Hybrid routing

---

# Related Documents

ARCH-05

ARCH-07