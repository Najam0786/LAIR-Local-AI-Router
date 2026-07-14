from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.providers.model_metadata import ModelMetadata


class CapabilityResolver:
    """
    Resolves capability profiles for AI models.

    When provider metadata is available, VISION/EMBEDDING/TOOL_USE and
    context_window are grounded in it. REASONING/CODING/TRANSLATION/
    SUMMARIZATION have no real data source anywhere yet, so they stay
    inferred from the model identifier regardless of metadata.
    """

    def resolve(
        self,
        model_id: str,
        provider: str,
        metadata: ModelMetadata | None = None,
    ) -> CapabilityProfile:
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

        is_vision = (
            metadata.is_vision
            if metadata is not None
            else ("vision" in model or "-vl" in model)
        )

        if is_vision:
            capabilities.append(
                Capability(type=CapabilityType.VISION)
            )

        # ---------------------------------------------------------
        # Embeddings
        # ---------------------------------------------------------

        is_embedding = (
            metadata.is_embedding
            if metadata is not None
            else ("embed" in model or "embedding" in model)
        )

        if is_embedding:
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

        # ---------------------------------------------------------
        # Tool Use (no heuristic exists for this -- metadata only)
        # ---------------------------------------------------------

        if metadata is not None and metadata.supports_tool_use:
            capabilities.append(
                Capability(type=CapabilityType.TOOL_USE)
            )

        return CapabilityProfile(
            model_id=model_id,
            provider=provider,
            capabilities=capabilities,
            context_window=(
                metadata.context_window if metadata is not None else None
            ),
        )


resolver = CapabilityResolver()
