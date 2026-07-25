from app.capabilities.capability import CapabilityType
from app.capabilities.requirement import CapabilityRequirement


class RequestAnalyzer:
    """
    Analyzes a user request and determines the required capabilities.

    This is the first stage of LAIR's routing pipeline.
    """

    def analyze(self, prompt: str) -> list[CapabilityRequirement]:
        """
        Analyze a prompt and return the required capabilities.
        """

        prompt = prompt.lower()

        requirements: list[CapabilityRequirement] = [
            CapabilityRequirement(
                capability=CapabilityType.TEXT_GENERATION,
            )
        ]

        # ---------------------------------------------------------
        # Vision
        # ---------------------------------------------------------

        if any(
            keyword in prompt
            for keyword in (
                "image",
                "photo",
                "picture",
                "vision",
                "ocr",
            )
        ):
            requirements.append(
                CapabilityRequirement(
                    capability=CapabilityType.VISION,
                )
            )

        # ---------------------------------------------------------
        # Coding
        # ---------------------------------------------------------

        if any(
            keyword in prompt
            for keyword in (
                "python",
                "code",
                "program",
                "bug",
                "debug",
                "function",
                "script",
            )
        ):
            requirements.append(
                CapabilityRequirement(
                    capability=CapabilityType.CODING,
                )
            )

        # ---------------------------------------------------------
        # Reasoning
        # ---------------------------------------------------------

        if any(
            keyword in prompt
            for keyword in (
                "reason",
                "analyze",
                "solve",
                "logic",
                "think",
            )
        ):
            requirements.append(
                CapabilityRequirement(
                    capability=CapabilityType.REASONING,
                )
            )

        # ---------------------------------------------------------
        # Translation
        # ---------------------------------------------------------

        if "translate" in prompt:
            requirements.append(
                CapabilityRequirement(
                    capability=CapabilityType.TRANSLATION,
                )
            )

        # ---------------------------------------------------------
        # Summarization
        # ---------------------------------------------------------

        if "summarize" in prompt or "summary" in prompt:
            requirements.append(
                CapabilityRequirement(
                    capability=CapabilityType.SUMMARIZATION,
                )
            )

        return requirements


analyzer = RequestAnalyzer()