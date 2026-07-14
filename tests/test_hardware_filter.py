from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.hardware.filter import filter_by_hardware
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.resource_profile import ResourceProfile
from app.models.ai_model import AIModel


def _model(model_id: str, loaded: bool = False) -> AIModel:
    return AIModel(
        id=model_id,
        provider="test",
        loaded=loaded,
        profile=CapabilityProfile(
            model_id=model_id,
            provider="test",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
        ),
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
