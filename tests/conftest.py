import pytest
from fastapi.testclient import TestClient

from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.hardware_provider import HardwareProvider
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.providers.base import BaseProvider
from app.providers.completion_result import CompletionResult
from app.registry.provider_registry import provider_registry
from app.routing.decision_repository import DecisionRepository
import app.routing.routing_engine as routing_engine_module
from main import app


class FakeHardwareProvider(HardwareProvider):
    """
    Test double reporting a fixed, generous HardwareProfile so tests
    never depend on this machine's actual, currently-in-use RAM.
    """

    def __init__(self, profile: HardwareProfile | None = None):
        self._profile = profile or HardwareProfile(
            total_ram_gb=1000.0,
            available_ram_gb=1000.0,
            gpu_vram_gb=None,
        )

    def detect(self) -> HardwareProfile:
        return self._profile


class FakeProvider(BaseProvider):
    """
    Test double standing in for a real inference backend.
    """

    name = "fake"

    def __init__(
        self,
        models: list[AIModel],
        completions: dict[str, CompletionResult] | None = None,
        failures: set[str] | None = None,
    ):
        self._models = models
        self._completions = completions or {}
        self._failures = failures or set()

    async def list_models(self) -> list[AIModel]:
        return self._models

    async def health_check(self) -> bool:
        return True

    async def complete(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 64,
    ) -> CompletionResult:
        if model_id in self._failures:
            raise RuntimeError(f"simulated failure for {model_id}")

        return self._completions.get(
            model_id,
            CompletionResult(text="ok", completion_tokens=8, latency_seconds=0.5),
        )


def _make_model(
    model_id: str,
    capabilities: list[CapabilityType],
    context_window: int | None,
    supports_streaming: bool = True,
) -> AIModel:
    return AIModel(
        id=model_id,
        provider="fake",
        profile=CapabilityProfile(
            model_id=model_id,
            provider="fake",
            capabilities=[Capability(type=c) for c in capabilities],
            context_window=context_window,
            supports_streaming=supports_streaming,
        ),
    )


FAKE_MODELS = [
    _make_model("qwen3-8b", [CapabilityType.TEXT_GENERATION], context_window=8192),
    _make_model(
        "qwen2.5-coder-32b",
        [CapabilityType.TEXT_GENERATION, CapabilityType.CODING],
        context_window=32768,
    ),
    _make_model(
        "deepseek-r1-distill-qwen-32b",
        [CapabilityType.TEXT_GENERATION, CapabilityType.REASONING],
        context_window=65536,
    ),
    _make_model(
        "qwen2.5-vl-7b",
        [CapabilityType.TEXT_GENERATION, CapabilityType.VISION],
        context_window=4096,
        supports_streaming=False,
    ),
]


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider(list(FAKE_MODELS))


@pytest.fixture
def clean_registry():
    """
    Empties the process-global provider registry for the duration
    of a test, then restores whatever was registered before.
    """

    original = dict(provider_registry._providers)
    provider_registry._providers.clear()

    yield provider_registry

    provider_registry._providers.clear()
    provider_registry._providers.update(original)


@pytest.fixture
def registered_fake_provider(clean_registry, fake_provider) -> FakeProvider:
    clean_registry.register(fake_provider)
    return fake_provider


@pytest.fixture(autouse=True)
def isolated_stores(tmp_path, monkeypatch):
    """
    Points the default KnowledgeBase and DecisionRepository at
    tmp_path-backed instances for every test, so nothing ever reads
    or writes the real benchmarks/knowledge_base.json or
    logs/decisions.json on disk.
    """

    monkeypatch.setattr(
        routing_engine_module,
        "default_knowledge_base",
        KnowledgeBase(path=tmp_path / "knowledge_base.json"),
    )
    monkeypatch.setattr(
        routing_engine_module,
        "default_decision_repository",
        DecisionRepository(path=tmp_path / "decisions.json"),
    )
    monkeypatch.setattr(
        routing_engine_module,
        "default_hardware_provider",
        FakeHardwareProvider(),
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
