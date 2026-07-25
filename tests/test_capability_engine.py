from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.engine import engine
from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement


def _profile(model_id: str, capabilities: list[Capability]) -> CapabilityProfile:
    return CapabilityProfile(
        model_id=model_id,
        provider="test",
        capabilities=capabilities,
    )


def test_matches_profile_with_required_capability():
    profiles = [
        _profile("a", [Capability(type=CapabilityType.CODING)]),
        _profile("b", [Capability(type=CapabilityType.TEXT_GENERATION)]),
    ]
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING)]

    matches = engine.find_matching_profiles(requirements, profiles)

    assert [profile.model_id for profile in matches] == ["a"]


def test_excludes_disabled_capability():
    profiles = [_profile("a", [Capability(type=CapabilityType.CODING, enabled=False)])]
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING)]

    assert engine.find_matching_profiles(requirements, profiles) == []


def test_excludes_profile_below_minimum_confidence():
    profiles = [_profile("a", [Capability(type=CapabilityType.CODING, confidence=0.2)])]
    requirements = [
        CapabilityRequirement(capability=CapabilityType.CODING, minimum_confidence=0.5)
    ]

    assert engine.find_matching_profiles(requirements, profiles) == []


def test_requires_all_requirements_to_match():
    profiles = [_profile("a", [Capability(type=CapabilityType.CODING)])]
    requirements = [
        CapabilityRequirement(capability=CapabilityType.CODING),
        CapabilityRequirement(capability=CapabilityType.VISION),
    ]

    assert engine.find_matching_profiles(requirements, profiles) == []
