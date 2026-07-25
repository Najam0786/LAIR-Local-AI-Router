from enum import Enum


class Provenance(str, Enum):
    """
    Origin of a routing score factor, surfaced in explanations so users
    can tell a measured fact from a declared default from a guess.
    """

    MEASURED = "measured"

    COMMUNITY = "community"

    DECLARED = "declared"

    HEURISTIC = "heuristic"

    MEMORY = "memory"
