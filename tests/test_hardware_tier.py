import pytest

from app.hardware.tier import HardwareTier, classify_tier


@pytest.mark.parametrize(
    "total_ram_gb,has_usable_gpu,expected",
    [
        (4.0, True, HardwareTier.ENTRY),
        (8.0, True, HardwareTier.ENTRY),
        (8.1, True, HardwareTier.STANDARD),
        (16.0, True, HardwareTier.STANDARD),
        (16.1, True, HardwareTier.ENTHUSIAST),
        (64.0, True, HardwareTier.ENTHUSIAST),
        # No usable GPU -> CPU_ONLY regardless of how much RAM exists.
        (4.0, False, HardwareTier.CPU_ONLY),
        (64.0, False, HardwareTier.CPU_ONLY),
    ],
)
def test_classify_tier(total_ram_gb, has_usable_gpu, expected):
    assert classify_tier(total_ram_gb, has_usable_gpu) == expected


def test_all_four_tiers_are_reachable():
    # Explicit mocked profiles covering each of the four tiers, per
    # I-02's acceptance criteria.
    profiles = {
        HardwareTier.ENTRY: (6.0, True),
        HardwareTier.STANDARD: (16.0, True),
        HardwareTier.ENTHUSIAST: (64.0, True),
        HardwareTier.CPU_ONLY: (16.0, False),
    }

    for expected_tier, (ram, gpu) in profiles.items():
        assert classify_tier(ram, gpu) == expected_tier
