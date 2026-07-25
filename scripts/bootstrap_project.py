from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

directories = [
    "docs",
    "scripts",
    "benchmarks",
    "configs",
    "logs",
    "prompts",
    "tests",
]

files = [
    "README.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "CONTRIBUTING.md",
    "LICENSE",
    ".env.example",
    ".gitignore",
    "docs/architecture.md",
    "docs/routing_engine.md",
    "docs/model_registry.md",
    "docs/providers.md",
    "docs/benchmarking.md",
    "docs/vision.md",
    "docs/design_decisions.md",
    "docs/ideas.md",
    "docs/api.md",
    "docs/principles.md",
]

for directory in directories:
    (ROOT / directory).mkdir(parents=True, exist_ok=True)

for file in files:
    path = ROOT / file
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.touch()

print("=" * 60)
print("LAIR Project Bootstrap Complete")
print("=" * 60)
print()

print("Directories:")
for d in directories:
    print(f"  ✓ {d}")

print()

print("Files:")
for f in files:
    print(f"  ✓ {f}")