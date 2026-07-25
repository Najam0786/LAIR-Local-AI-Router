import re

from app.hardware.resource_profile import ResourceProfile
from app.providers.model_metadata import ModelMetadata

_PARAM_COUNT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)b", re.IGNORECASE)

# Matches the "-A3B"/"-A4B"-style suffix LAIR's own MoE portfolio
# entries use (e.g. "qwen3.6-35b-a3b") to name active (not total)
# parameters. Requires a leading "a" so it never matches the base
# total-parameter count itself (e.g. the "35b" in the same id).
_ACTIVE_PARAM_PATTERN = re.compile(r"[-_]a(\d+(?:\.\d+)?)b(?![a-z0-9])", re.IGNORECASE)


def detect_moe(model_id: str) -> tuple[bool, float | None]:
    """
    Heuristically detects whether a model id names itself as MoE via the
    "-A<n>B" active-parameter suffix convention, and if so, the active
    parameter count in billions.

    Id-pattern heuristic only (I-03) -- no provider exposes MoE-ness or
    active parameter count as real metadata today. Deliberately doesn't
    feed a memory-estimate reduction: LAIR doesn't yet control whether
    expert-offload is actually enabled in the backend, and guessing a
    smaller footprint than what's really resident risks real OOM
    (ADR-0011) -- it only informs the routing explanation.
    """

    match = _ACTIVE_PARAM_PATTERN.search(model_id)

    if not match:
        return False, None

    return True, float(match.group(1))


def detect_streamable(is_moe: bool) -> bool:
    """
    Heuristic streamable-candidate flag for I-16's SSD-streaming
    routing tier (ADR-0021): MoE is the priority streamable class per
    the plan's own research (few active params/token means most of a
    partially-mmap'd model's weights are simply never touched for a
    given token) -- a dense model needing the same full-weight
    streaming would be far too slow to be worth surfacing this pass.
    """

    return is_moe


# Rough placeholder estimate assuming typical quantization, in GB per
# billion parameters. Used when quantization is unknown or unrecognized.
# Not a measurement -- meant to be replaced once real benchmark-derived
# memory metadata exists.
_DEFAULT_GB_PER_BILLION_PARAMS = 0.7

# Approximate GB per billion parameters by GGUF quantization family.
# Still a heuristic -- doesn't account for KV-cache overhead or exact
# bits-per-weight -- but grounded in real reported quantization data
# rather than one flat constant for every model.
_GB_PER_BILLION_BY_QUANTIZATION_PREFIX: list[tuple[str, float]] = [
    ("Q4", 0.55),
    ("Q5", 0.7),
    ("Q6", 0.8),
    ("Q8", 1.1),
    ("F16", 2.0),
    ("FP16", 2.0),
    ("F32", 4.0),
]


def _gb_per_billion_params(quantization: str | None) -> float:
    if quantization is None:
        return _DEFAULT_GB_PER_BILLION_PARAMS

    upper = quantization.upper()

    for prefix, gb_per_billion in _GB_PER_BILLION_BY_QUANTIZATION_PREFIX:
        if upper.startswith(prefix):
            return gb_per_billion

    return _DEFAULT_GB_PER_BILLION_PARAMS


# Bytes of fp16 KV cache per token, per billion parameters -- calibrated
# from Llama-2-7B's real, published architecture (32 layers, hidden
# size 4096, standard multi-head attention, fp16):
#   2 (K and V) * 32 layers * 4096 hidden * 2 bytes = 524,288 bytes/token
#   524,288 / 7 (billion params) ~= 74,898 bytes/token/billion-params
#
# This is a deliberately conservative *upper bound* for I-17, not a
# per-architecture measurement: most of LAIR's actual portfolio (Qwen,
# Gemma, DeepSeek) uses grouped-query attention, which needs meaningfully
# *less* KV cache per token than the MHA architecture this constant is
# calibrated from -- so real usage should fit at least as well as this
# estimate predicts, never worse (ADR-0011/ADR-0012's established
# "wrong rejection is worse than a missed one, but a wrong acceptance
# is worse still for a hard constraint" reasoning: overestimating a
# hard memory constraint is the safe direction, underestimating it
# risks real OOM exactly like docs/DOGFOODING.md DF-006 point 3 showed
# happens in practice).
_KV_FP16_BYTES_PER_TOKEN_PER_BILLION_PARAMS = 74_898.0

_BYTES_PER_GB = 1024**3

# Relative byte cost of each KV-cache precision vs. fp16.
_KV_QUANT_FRACTIONS: list[tuple[str, float]] = [
    ("fp16", 1.0),
    ("int8", 0.5),
    ("q4", 0.25),
]


def _kv_cache_gb(params_billions: float, context_length: int, fraction: float) -> float:
    bytes_total = (
        params_billions
        * context_length
        * _KV_FP16_BYTES_PER_TOKEN_PER_BILLION_PARAMS
        * fraction
    )
    return bytes_total / _BYTES_PER_GB


class ResourceResolver:
    """
    Resolves resource profiles for AI models.

    Parameter count is always inferred from the model identifier --
    there is no other source for it yet. When provider metadata
    includes quantization, the memory estimate uses a quantization-
    aware figure instead of one flat constant for every model.
    """

    def resolve(
        self,
        model_id: str,
        metadata: ModelMetadata | None = None,
        context_window: int | None = None,
        available_ram_gb: float | None = None,
    ) -> ResourceProfile:
        """
        Build a ResourceProfile for the given model.

        `context_window`, when given, adds a KV-cache-aware fit
        calculation (I-17): weights + fp16 KV cache at that context
        length. `available_ram_gb`, when also given, additionally
        computes the smallest KV precision (fp16/int8/q4) that would
        let this model's full configured context fit within it.
        """

        match = _PARAM_COUNT_PATTERN.search(model_id)

        if not match:
            return ResourceProfile(estimated_ram_gb=None)

        params_billions = float(match.group(1))

        quantization = metadata.quantization if metadata is not None else None

        estimated_ram_gb = params_billions * _gb_per_billion_params(quantization)

        if not context_window:
            return ResourceProfile(estimated_ram_gb=estimated_ram_gb)

        kv_cache_gb = _kv_cache_gb(params_billions, context_window, fraction=1.0)

        kv_cache_quant_recommended = None
        if available_ram_gb is not None:
            kv_cache_quant_recommended = self.recommend_kv_quant(
                params_billions, context_window, estimated_ram_gb, available_ram_gb
            )

        return ResourceProfile(
            estimated_ram_gb=estimated_ram_gb,
            estimated_kv_cache_gb=kv_cache_gb,
            estimated_total_ram_gb=estimated_ram_gb + kv_cache_gb,
            kv_cache_quant_recommended=kv_cache_quant_recommended,
        )

    def recommend_kv_quant(
        self,
        params_billions: float,
        context_window: int,
        weights_gb: float,
        available_ram_gb: float,
    ) -> str | None:
        """
        The least-lossy KV precision that fits `weights_gb` plus KV
        cache at `context_window` tokens within `available_ram_gb`, or
        None if even the smallest (q4) still wouldn't fit.
        """

        for name, fraction in _KV_QUANT_FRACTIONS:
            kv_gb = _kv_cache_gb(params_billions, context_window, fraction)

            if weights_gb + kv_gb <= available_ram_gb:
                return name

        return None


resource_resolver = ResourceResolver()
