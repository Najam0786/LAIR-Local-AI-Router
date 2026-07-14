def test_route_without_providers_returns_503(client, clean_registry):
    response = client.post("/route", json={"prompt": "hello"})

    assert response.status_code == 503


def test_route_happy_path(client, registered_fake_provider):
    response = client.post(
        "/route", json={"prompt": "please debug this python function"}
    )

    assert response.status_code == 200

    plan = response.json()["plan"]

    assert plan["steps"][0]["role"] == "primary"
    assert plan["steps"][0]["model_id"] == "qwen2.5-coder-32b"
    assert 0.0 <= plan["decision"]["confidence"] <= 1.0
    assert plan["decision"]["reasons"]


def test_route_routes_even_when_no_model_has_the_requested_capability(
    client, registered_fake_provider
):
    # Capability matching is a soft scoring preference, not a hard filter --
    # a request for a capability no registered model has still routes to
    # the best-available candidate rather than 404ing.
    response = client.post(
        "/route", json={"prompt": "translate this sentence to french"}
    )

    assert response.status_code == 200


def test_route_excludes_model_that_exceeds_available_ram(
    client, clean_registry, monkeypatch
):
    import app.routing.routing_engine as routing_engine_module
    from app.capabilities.capability import Capability, CapabilityType
    from app.capabilities.profile import CapabilityProfile
    from app.hardware.hardware_profile import HardwareProfile
    from app.models.ai_model import AIModel
    from tests.conftest import FakeHardwareProvider, FakeProvider

    # Not loaded -- exercises the RAM-fit check itself, rather than the
    # already-loaded-models-are-always-kept path (a loaded model's
    # memory is already allocated, so the RAM check doesn't apply to it).
    oversized_model = AIModel(
        id="qwen2.5-coder-70b",
        provider="fake",
        loaded=False,
        profile=CapabilityProfile(
            model_id="qwen2.5-coder-70b",
            provider="fake",
            capabilities=[
                Capability(type=CapabilityType.TEXT_GENERATION),
                Capability(type=CapabilityType.CODING),
            ],
        ),
    )
    clean_registry.register(FakeProvider([oversized_model]))

    monkeypatch.setattr(
        routing_engine_module,
        "default_hardware_provider",
        FakeHardwareProvider(
            HardwareProfile(total_ram_gb=16.0, available_ram_gb=1.0)
        ),
    )

    response = client.post(
        "/route", json={"prompt": "please debug this python function"}
    )

    assert response.status_code == 404
