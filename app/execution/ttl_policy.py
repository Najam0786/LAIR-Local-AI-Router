from app.hardware.resource_resolver import ResourceResolver, resource_resolver
from app.models.ai_model import AIModel

# LM Studio's own default idle TTL (60 minutes). Applied to models LAIR
# treats as this machine's fast/generalist role -- worth keeping warm
# since they're reused constantly (I-05).
GENERALIST_TTL_SECONDS = 3600

# Shorter TTL for large specialist models: release their RAM promptly
# once idle instead of holding it until the next JIT load evicts them.
# 30 minutes, not 5 (DF-007): 5 minutes was shorter than normal IDE
# think-time between messages, so an interactive session kept evicting
# and JIT-reloading a 20-35GB model mid-conversation -- the reload, not
# inference, was the dominant source of perceived latency in Continue.
SPECIALIST_TTL_SECONDS = 1800

# Below this estimated footprint, a model is treated as this machine's
# fast/generalist role regardless of which specific model it is.
GENERALIST_RAM_THRESHOLD_GB = 10.0


class TtlPolicy:
    """
    Decides the per-request `ttl` (idle-unload seconds) LM Studio should
    apply to a model, based on its estimated size.

    Cooperates with LM Studio's own JIT loading / Auto-Evict (ADR-0013,
    DF-006) rather than replacing them: this only tunes how long an idle
    model is allowed to sit loaded, not whether/when it loads or evicts.
    """

    def __init__(self, resolver: ResourceResolver | None = None):
        self._resolver = resolver or resource_resolver

    def ttl_seconds_for(self, model: AIModel) -> int:
        profile = self._resolver.resolve(model.id, model.metadata)

        if (
            profile.estimated_ram_gb is not None
            and profile.estimated_ram_gb > GENERALIST_RAM_THRESHOLD_GB
        ):
            return SPECIALIST_TTL_SECONDS

        return GENERALIST_TTL_SECONDS


default_ttl_policy = TtlPolicy()
