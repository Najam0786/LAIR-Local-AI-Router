from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile


class CapabilityResolver:
    """
    Resolves capability profiles for AI models.

    Initially, capabilities are inferred from the model identifier.
    In future versions, this resolver will support metadata files,
    benchmarks, provider APIs, and user-defined overrides.
    """

    def resolve(self, model_id: str, provider: str) -> CapabilityProfile:
        """
        Build a CapabilityProfile for the given model.
        """

        capabilities: list[Capability] = [
            Capability(type=CapabilityType.TEXT_GENERATION),
        ]

        model = model_id.lower()

        # ---------------------------------------------------------
        # Reasoning
        # ---------------------------------------------------------

        if "deepseek" in model or "r1" in model:
            capabilities.append(
                Capability(type=CapabilityType.REASONING)
            )

        # ---------------------------------------------------------
        # Vision
        # ---------------------------------------------------------

        if "vision" in model or "-vl" in model:
            capabilities.append(
                Capability(type=CapabilityType.VISION)
            )

        # ---------------------------------------------------------
        # Embeddings
        # ---------------------------------------------------------

        if "embed" in model or "embedding" in model:
            capabilities.append(
                Capability(type=CapabilityType.EMBEDDING)
            )

        # ---------------------------------------------------------
        # Coding
        # ---------------------------------------------------------

        if "coder" in model or "code" in model:
            capabilities.append(
                Capability(type=CapabilityType.CODING)
            )

        return CapabilityProfile(
            model_id=model_id,
            provider=provider,
            capabilities=capabilities,
        )


resolver = CapabilityResolver()