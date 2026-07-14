import re

from app.hardware.resource_profile import ResourceProfile
from app.providers.model_metadata import ModelMetadata

_PARAM_COUNT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)b", re.IGNORECASE)

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
    ) -> ResourceProfile:
        """
        Build a ResourceProfile for the given model.
        """

        match = _PARAM_COUNT_PATTERN.search(model_id)

        if not match:
            return ResourceProfile(estimated_ram_gb=None)

        params_billions = float(match.group(1))

        quantization = metadata.quantization if metadata is not None else None

        return ResourceProfile(
            estimated_ram_gb=(
                params_billions * _gb_per_billion_params(quantization)
            )
        )


resource_resolver = ResourceResolver()
