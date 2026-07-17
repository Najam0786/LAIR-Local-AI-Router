# 🚀 LAIR — Local AI Intelligence Router

> **Build intelligently. Measure everything. Evolve continuously.**

---

## Overview

Today's AI developers often work with multiple language models.

One model excels at coding.

Another performs better at reasoning.

A third specializes in vision.

A fourth handles long-context documentation.

Choosing the right model manually is inefficient and quickly becomes difficult as the number of available models grows.

**LAIR (Local AI Intelligence Router)** solves this problem by automatically selecting the most appropriate AI model for every task using capability-aware, benchmark-driven and explainable routing.

Rather than asking:

> "Which model should I use?"

Users simply describe the task.

LAIR decides the rest.

---

# Why LAIR?

Modern AI workflows are becoming increasingly heterogeneous.

Different models excel at different tasks.

Examples include:

| Task | Example Models |
|-------|----------------|
| Coding | Qwen3.6 |
| Documentation | Gemma 4 |
| Deep Reasoning | DeepSeek-R1 |
| Vision | Qwen2.5-VL |
| Fast Assistance | Qwen3 8B |

Instead of manually switching models, LAIR automatically selects the best execution strategy.

---

# Key Features

- Local-first AI orchestration
- Provider-agnostic architecture
- Intelligent capability-based routing
- Benchmark-driven model selection
- Explainable routing decisions
- Long-context support
- Multi-model execution (planned)
- Learning engine (planned)
- Plugin architecture (planned)

---

# High-Level Architecture

```
                  User
                    │
                    ▼
          Capability Engine
                    │
                    ▼
            Routing Engine
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Qwen        Gemma      DeepSeek
        │           │           │
        └───────────┼───────────┘
                    ▼
             Best Response
```

---

# Project Structure

```
LAIR/

├── app/
├── benchmarks/
├── configs/
├── docs/
├── logs/
├── prompts/
├── scripts/
├── tests/

├── README.md
├── ROADMAP.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
```

---

# Documentation

The complete project documentation is located in the **docs/** directory.

Start here:

```
docs/index.md
```

Documentation includes:

- Product Vision
- Project Charter
- Engineering Handbook
- Architecture
- Routing Engine
- Model Registry
- Provider Architecture
- API Specification
- Benchmarking Framework
- ADRs
- RFCs
- Research
- Innovation Backlog

---

# Current Model Portfolio

| Role | Model |
|------|-------|
| Coding | Qwen3.6 35B A3B |
| Documentation | Gemma 4 26B A4B |
| Deep Reasoning | DeepSeek-R1 Distill Qwen 32B |
| Vision | Qwen2.5-VL 7B |
| Fast Assistant | Qwen3 8B |

---

# Technology Stack

- Python 3.13+
- FastAPI
- LM Studio
- Pydantic
- HTTPX
- Uvicorn

Planned:

- Ollama
- vLLM
- OpenAI-compatible providers
- Docker
- Kubernetes

---

# Development Status

Current Version

```
v0.1.0-alpha
```

Current Phase

```
Architecture Foundation Complete
```

Next Milestone

```
Capability Engine
```

---

# Roadmap

| Version | Focus |
|----------|-------|
| 0.1 | Architecture Foundation |
| 0.2 | Capability Engine |
| 0.3 | Intelligent Routing |
| 0.4 | Benchmark Engine |
| 0.5 | Multi-Provider |
| 0.6 | Learning Engine |
| 1.0 | Public Release |

More details are available in:

```
ROADMAP.md
```

---

# Quick Start

Clone the repository

```bash
git clone https://github.com/Najam0786/LAIR-Local-AI-Router.git
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies

```bash
pip install -r requirements.txt
```

Start the server

```bash
uvicorn main:app --reload
```

Open

```
http://localhost:8000/docs
```

For LM Studio setup, connecting a chat client (e.g. Continue), configuration
options, and troubleshooting, see **[INSTRUCTIONS.md](INSTRUCTIONS.md)**.

---

# Engineering Philosophy

LAIR follows a structured engineering workflow.

```
Innovation

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

Release
```

Architecture precedes implementation.

Evidence precedes optimization.

---

# Contributing

Contributions are welcome.

Before implementing significant features, contributors should review:

- Project Charter
- Engineering Handbook
- Innovation Backlog
- ADR Guidelines
- RFC Process

---

# License

This project is released under the MIT License.

See:

```
LICENSE
```

---

# Acknowledgements

LAIR builds upon the excellent work of the open-source AI community, including:

- LM Studio
- FastAPI
- Pydantic
- Hugging Face
- Qwen
- Google Gemma
- DeepSeek

---

# Mission

Create the world's most capable open-source platform for intelligent local AI orchestration.

Provider-agnostic.

Benchmark-driven.

Explainable.

Local-first.

---

> **"The best model is not the biggest model. It's the right model for the task."**