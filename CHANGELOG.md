# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and the project follows Semantic Versioning.

---

## [Unreleased]

### Added

- Capability Engine foundation
- Capability domain models
- Provider Registry
- AIModel domain model
- Capability Profile abstraction
- Capability Requirement abstraction

### Changed

- Refactored `BaseProvider` to return `AIModel` objects instead of raw dictionaries.
- Refactored LM Studio provider to use the domain model.
- Refactored `ModelRegistry` to use the new `ProviderRegistry`.
- Expanded application configuration for future providers and routing.

---

## [0.1.0-alpha] - 2026-07-13

### Added

- Initial FastAPI application structure
- LM Studio provider
- Provider abstraction layer
- Model registry
- Health API
- Models API
- Architecture documentation
- Engineering handbook
- Product vision
- Project charter
- Routing engine design
- Benchmarking design
- ADR framework
- RFC framework
- Research framework
- Innovation backlog
- Repository governance
- GitHub Release `v0.1.0-alpha`