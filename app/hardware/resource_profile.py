from pydantic import BaseModel


class ResourceProfile(BaseModel):
    """
    Estimated resource requirement for running a model.
    """

    estimated_ram_gb: float | None = None

    # KV-cache estimate at the model's currently-configured context
    # window (ModelMetadata.context_window), assuming fp16 KV -- and
    # the weights+KV total that implies. None when context length is
    # unknown, or (I-17) unchanged from `estimated_ram_gb` for callers
    # that never populate them.
    estimated_kv_cache_gb: float | None = None
    estimated_total_ram_gb: float | None = None

    # The smallest KV-cache precision (fp16/int8/q4) LAIR estimates
    # would let this model's full configured context fit in a given
    # amount of RAM -- None if even q4 KV wouldn't help, or if KV
    # wasn't estimated at all. Purely a recommendation for the user to
    # apply in LM Studio's own load settings (I-17) -- no verified
    # LM Studio request-level API sets this per-request the way `ttl`
    # or `draft_model` do, so LAIR doesn't claim to set it.
    kv_cache_quant_recommended: str | None = None

    @property
    def effective_ram_gb(self) -> float | None:
        """
        The RAM figure hardware-fit checks should actually use: the
        weights+KV total when known, falling back to weights alone --
        so callers that never populated KV fields (e.g. existing tests,
        or resolutions with an unknown context length) keep working
        exactly as before I-17.
        """

        if self.estimated_total_ram_gb is not None:
            return self.estimated_total_ram_gb

        return self.estimated_ram_gb
