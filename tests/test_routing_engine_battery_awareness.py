from app.core.settings import settings
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.task import Task
import app.routing.routing_engine as routing_engine_module
from app.routing.routing_engine import RoutingEngine
from tests.conftest import FAKE_MODELS


def test_battery_awareness_disabled_never_adds_the_factor(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "ENABLE_BATTERY_AWARENESS", False)
    monkeypatch.setattr(
        routing_engine_module, "read_power_state", lambda: (_ for _ in ()).throw(
            AssertionError("read_power_state should not be called when disabled")
        )
    )

    engine = RoutingEngine()
    plan = engine.route(
        task=Task(prompt="hello there, general question"),
        models=[FAKE_MODELS[0]],
        knowledge_base=KnowledgeBase(path=tmp_path / "kb.json"),
    )

    winner = plan.decision.candidates[0]
    assert not any(f.name == "battery_awareness" for f in winner.breakdown.factors)


def test_battery_awareness_enabled_reads_real_power_state(monkeypatch, tmp_path):
    from app.hardware.power import PowerState

    monkeypatch.setattr(settings, "ENABLE_BATTERY_AWARENESS", True)
    monkeypatch.setattr(
        routing_engine_module,
        "read_power_state",
        lambda: PowerState(on_battery=True, battery_percent=20.0),
    )

    engine = RoutingEngine()
    plan = engine.route(
        task=Task(prompt="hello there, general question"),
        models=[FAKE_MODELS[0]],
        knowledge_base=KnowledgeBase(path=tmp_path / "kb.json"),
    )

    winner = plan.decision.candidates[0]
    assert any(f.name == "battery_awareness" for f in winner.breakdown.factors)
