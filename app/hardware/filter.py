from app.core.settings import settings
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.resource_profile import ResourceProfile
from app.models.ai_model import AIModel


def filter_by_hardware(
    models: list[AIModel],
    resource_profiles: dict[str, ResourceProfile],
    hardware: HardwareProfile,
    streaming_viability: float | None = None,
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

    The fit check uses `ResourceProfile.effective_ram_gb` (weights + KV
    cache at the model's configured context length when known, I-17) --
    the same weights-only figure as before I-17 for any profile that
    never populated KV fields, so existing callers are unaffected.
    """

    reclaimable_ram_gb = sum(
        resource_profiles[model.id].effective_ram_gb
        for model in models
        if model.loaded
        and resource_profiles.get(model.id) is not None
        and resource_profiles[model.id].effective_ram_gb is not None
    )

    kept: list[AIModel] = []

    for model in models:
        if model.loaded:
            kept.append(model)
            continue

        profile = resource_profiles.get(model.id)

        if profile is None or profile.effective_ram_gb is None:
            kept.append(model)
            continue

        if profile.effective_ram_gb <= hardware.available_ram_gb + reclaimable_ram_gb:
            kept.append(model)
            continue

        # I-16 (ADR-0021): a model that doesn't fit in RAM is still
        # kept, at a heavy scoring penalty (ModelScorer), when it's a
        # declared streaming candidate and this machine's measured SSD
        # viability clears the configured bar -- "slow but possible" is
        # an explicit, explained routing tier, not a silent exclusion.
        # Off by default (ENABLE_STREAMING_ROUTING); a hard exclusion
        # otherwise, unchanged from pre-I-16 behavior.
        if (
            settings.ENABLE_STREAMING_ROUTING
            and streaming_viability is not None
            and streaming_viability >= settings.STREAMING_MIN_VIABILITY
            and model.metadata is not None
            and model.metadata.streamable
        ):
            estimated_latency_multiplier = profile.effective_ram_gb / max(
                hardware.available_ram_gb + reclaimable_ram_gb, 0.01
            )

            if estimated_latency_multiplier <= settings.STREAMING_MAX_LATENCY_MULTIPLIER:
                kept.append(model)

    return kept
