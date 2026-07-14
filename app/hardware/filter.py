from app.hardware.hardware_profile import HardwareProfile
from app.hardware.resource_profile import ResourceProfile
from app.models.ai_model import AIModel


def filter_by_hardware(
    models: list[AIModel],
    resource_profiles: dict[str, ResourceProfile],
    hardware: HardwareProfile,
) -> list[AIModel]:
    """
    Keep only models that fit within available hardware.

    A model with an unknown resource profile is kept -- unknown means
    "don't filter on this dimension," not "assume the worst" (ADR-0011).
    A wrong rejection is worse than a missed one for a hard constraint.

    An already-loaded model is always kept: its memory is already
    allocated and it is proven to be running right now, so checking its
    estimated requirement against *remaining* free memory would wrongly
    penalize it for memory it isn't asking to allocate again. The check
    only makes sense for a model that would need fresh allocation to load.

    An unloaded candidate is checked against available RAM *plus*
    whatever RAM would be reclaimed by evicting any already-loaded
    models -- LM Studio's JIT loading auto-evicts the previously
    JIT-loaded model when a new one is requested, so that memory is
    about to become free, not permanently unavailable.
    """

    reclaimable_ram_gb = sum(
        resource_profiles[model.id].estimated_ram_gb
        for model in models
        if model.loaded
        and resource_profiles.get(model.id) is not None
        and resource_profiles[model.id].estimated_ram_gb is not None
    )

    kept: list[AIModel] = []

    for model in models:
        if model.loaded:
            kept.append(model)
            continue

        profile = resource_profiles.get(model.id)

        if profile is None or profile.estimated_ram_gb is None:
            kept.append(model)
            continue

        if profile.estimated_ram_gb <= hardware.available_ram_gb + reclaimable_ram_gb:
            kept.append(model)

    return kept
