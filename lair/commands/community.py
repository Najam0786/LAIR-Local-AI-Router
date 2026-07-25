from app.hardware.tier import HardwareTier
from app.registry.community_scores import export_contribution


def export(tier: HardwareTier) -> str:
    """
    Produces this machine's shareable, anonymized benchmark export
    (I-12) -- model id, hardware tier, and measured tokens/sec only.
    See configs/community_scores/README.md for how to contribute it.
    """

    return export_contribution(tier)
