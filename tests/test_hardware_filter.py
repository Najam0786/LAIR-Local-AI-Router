from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.core.settings import settings
from app.hardware.filter import filter_by_hardware
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.resource_profile import ResourceProfile
from app.models.ai_model import AIModel
from app.providers.model_metadata import ModelMetadata


def _model(
    model_id: str, loaded: bool = False, metadata: ModelMetadata | None = None
) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=loaded,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
        ),
        metadata=metadata,
    )


def test_unloaded_model_exceeding_available_ram_is_filtered_out():
    big = _model("big", loaded=False)
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    resource_profiles = {"big": ResourceProfile(estimated_ram_gb=22.4)}

    kept = filter_by_hardware([big], resource_profiles, hardware)

    assert kept == []


def test_unloaded_model_within_available_ram_is_kept():
    small = _model("small", loaded=False)
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=8.0)
    resource_profiles = {"small": ResourceProfile(estimated_ram_gb=4.0)}

    kept = filter_by_hardware([small], resource_profiles, hardware)

    assert kept == [small]


def test_unloaded_model_with_unknown_resource_profile_is_kept():
    unknown = _model("unknown", loaded=False)
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=1.0)
    resource_profiles = {"unknown": ResourceProfile(estimated_ram_gb=None)}

    kept = filter_by_hardware([unknown], resource_profiles, hardware)

    assert kept == [unknown]


def test_unloaded_model_missing_from_resource_profiles_is_kept():
    missing = _model("missing", loaded=False)
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=1.0)

    kept = filter_by_hardware([missing], {}, hardware)

    assert kept == [missing]


def test_already_loaded_model_is_kept_regardless_of_estimated_ram():
    big_but_running = _model("big-but-running", loaded=True)
    hardware = HardwareProfile(total_ram_gb=32.0, available_ram_gb=1.0)
    resource_profiles = {
        "big-but-running": ResourceProfile(estimated_ram_gb=22.4)
    }

    kept = filter_by_hardware([big_but_running], resource_profiles, hardware)

    assert kept == [big_but_running]


def test_unloaded_model_fits_once_loaded_models_reclaimable_ram_is_counted():
    currently_loaded = _model("currently-loaded", loaded=True)
    swap_candidate = _model("swap-candidate", loaded=False)
    # Only 6GB free right now, but the loaded model (15GB) would be
    # evicted by JIT loading, so the real candidate (20GB) fits once
    # that's accounted for (6 + 15 = 21 >= 20).
    hardware = HardwareProfile(total_ram_gb=32.0, available_ram_gb=6.0)
    resource_profiles = {
        "currently-loaded": ResourceProfile(estimated_ram_gb=15.0),
        "swap-candidate": ResourceProfile(estimated_ram_gb=20.0),
    }

    kept = filter_by_hardware(
        [currently_loaded, swap_candidate], resource_profiles, hardware
    )

    assert kept == [currently_loaded, swap_candidate]


def test_kv_aware_total_ram_can_reject_a_model_weights_alone_would_pass():
    # Weights alone (10GB) would fit in 12GB free, but weights + KV
    # cache at this model's configured context (I-17) don't.
    big_context_model = _model("big-context-model", loaded=False)
    hardware = HardwareProfile(total_ram_gb=32.0, available_ram_gb=12.0)
    resource_profiles = {
        "big-context-model": ResourceProfile(
            estimated_ram_gb=10.0,
            estimated_kv_cache_gb=5.0,
            estimated_total_ram_gb=15.0,
        )
    }

    kept = filter_by_hardware([big_context_model], resource_profiles, hardware)

    assert kept == []


def test_effective_ram_gb_falls_back_to_weights_only_when_kv_unknown():
    # A profile that never populated KV fields (pre-I-17 callers, or an
    # unknown context length) behaves exactly as before I-17.
    model = _model("plain-model", loaded=False)
    hardware = HardwareProfile(total_ram_gb=32.0, available_ram_gb=12.0)
    resource_profiles = {"plain-model": ResourceProfile(estimated_ram_gb=10.0)}

    kept = filter_by_hardware([model], resource_profiles, hardware)

    assert kept == [model]


def test_unloaded_model_still_rejected_if_it_would_not_fit_even_after_eviction():
    currently_loaded = _model("currently-loaded", loaded=True)
    too_big = _model("too-big", loaded=False)
    hardware = HardwareProfile(total_ram_gb=32.0, available_ram_gb=2.0)
    resource_profiles = {
        "currently-loaded": ResourceProfile(estimated_ram_gb=15.0),
        "too-big": ResourceProfile(estimated_ram_gb=25.0),
    }

    kept = filter_by_hardware(
        [currently_loaded, too_big], resource_profiles, hardware
    )

    assert kept == [currently_loaded]


def test_streaming_allowance_disabled_by_default_still_rejects_oversized(monkeypatch):
    assert settings.ENABLE_STREAMING_ROUTING is False

    big = _model("big", loaded=False, metadata=ModelMetadata(streamable=True))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    resource_profiles = {"big": ResourceProfile(estimated_ram_gb=22.4)}

    kept = filter_by_hardware([big], resource_profiles, hardware, streaming_viability=0.9)

    assert kept == []


def test_streaming_allowance_admits_streamable_model_when_viability_and_latency_clear(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_STREAMING_ROUTING", True)

    big = _model("big", loaded=False, metadata=ModelMetadata(streamable=True))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    # 4x the available RAM -- within the default 8x latency multiplier bar.
    resource_profiles = {"big": ResourceProfile(estimated_ram_gb=16.0)}

    kept = filter_by_hardware([big], resource_profiles, hardware, streaming_viability=0.9)

    assert kept == [big]


def test_streaming_allowance_rejects_non_streamable_model(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_STREAMING_ROUTING", True)

    big = _model("big", loaded=False, metadata=ModelMetadata(streamable=False))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    resource_profiles = {"big": ResourceProfile(estimated_ram_gb=16.0)}

    kept = filter_by_hardware([big], resource_profiles, hardware, streaming_viability=0.9)

    assert kept == []


def test_streaming_allowance_rejects_when_viability_below_bar(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_STREAMING_ROUTING", True)

    big = _model("big", loaded=False, metadata=ModelMetadata(streamable=True))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    resource_profiles = {"big": ResourceProfile(estimated_ram_gb=16.0)}

    kept = filter_by_hardware([big], resource_profiles, hardware, streaming_viability=0.1)

    assert kept == []


def test_streaming_allowance_rejects_when_latency_multiplier_too_high(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_STREAMING_ROUTING", True)

    way_too_big = _model("way-too-big", loaded=False, metadata=ModelMetadata(streamable=True))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    # 40x available RAM -- far beyond the default 8x latency multiplier bar.
    resource_profiles = {"way-too-big": ResourceProfile(estimated_ram_gb=160.0)}

    kept = filter_by_hardware(
        [way_too_big], resource_profiles, hardware, streaming_viability=0.9
    )

    assert kept == []
