from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement


class CapabilityEngine:
    """
    Evaluates AI model capability profiles against request requirements.
    """

    def find_matching_profiles(
        self,
        requirements: list[CapabilityRequirement],
        profiles: list[CapabilityProfile],
    ) -> list[CapabilityProfile]:
        """
        Return every capability profile that satisfies all requirements.
        """

        matches: list[CapabilityProfile] = []

        for profile in profiles:
            available = {
                capability.type: capability
                for capability in profile.capabilities
                if capability.enabled
            }

            if all(
                (
                    requirement.capability in available
                    and available[
                        requirement.capability
                    ].confidence >= requirement.minimum_confidence
                )
                for requirement in requirements
            ):
                matches.append(profile)

        return matches


engine = CapabilityEngine()