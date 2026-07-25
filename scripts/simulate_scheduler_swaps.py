"""
I-05 validation: demonstrates that the sticky "loaded" bonus in
ModelScorer measurably reduces model swaps on a simulated mixed
workload, compared to routing the same workload with the bonus
disabled (RoutingPolicy.loaded_bonus_weight = 0).

Offline and deterministic -- no running LM Studio required. Model
"loaded" state is simulated locally: after each routed decision, that
decision's model becomes the only "loaded" one for the next request.
"""

from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.policy import RoutingPolicy
from app.routing.routing_engine import routing_engine

# A small stand-in portfolio, shaped like LAIR's real one: one fast
# generalist plus a few larger specialists.
PORTFOLIO = [
    ("qwen3-8b", [CapabilityType.TEXT_GENERATION]),
    ("qwen3.6-35b-a3b", [CapabilityType.TEXT_GENERATION, CapabilityType.CODING]),
    (
        "deepseek-r1-distill-qwen-32b",
        [CapabilityType.TEXT_GENERATION, CapabilityType.REASONING],
    ),
    ("qwen2.5-vl-7b", [CapabilityType.TEXT_GENERATION, CapabilityType.VISION]),
]

# A realistic mixed workload: mostly ordinary chat turns (which any
# model satisfies equally well), with occasional capability-specific
# requests interspersed -- the pattern a single interactive user
# actually produces, not an adversarial worst case.
PROMPTS = [
    "hello, how are you",
    "what's the weather like conceptually",
    "please debug this python function",
    "tell me a fun fact",
    "how's it going",
    "analyze and solve this logic puzzle",
    "what's up",
    "quick chat, nothing special",
    "describe this image",
    "another casual question",
    "one more debug this script please",
    "just saying hi",
]


def _build_models(loaded_id: str | None) -> list[AIModel]:
    return [
        AIModel(
            id=model_id,
            provider="sim",
            loaded=(model_id == loaded_id),
            profile=CapabilityProfile(
                model_id=model_id,
                provider="sim",
                capabilities=[Capability(type=c) for c in capabilities],
                supports_streaming=True,
                context_window=32768,
            ),
        )
        for model_id, capabilities in PORTFOLIO
    ]


def _simulate(policy: RoutingPolicy) -> int:
    loaded_id: str | None = None
    swaps = 0

    for prompt in PROMPTS:
        models = _build_models(loaded_id)
        plan = routing_engine.route(Task(prompt=prompt), models, policy=policy)
        selected_id = plan.decision.selected_model.id

        if loaded_id is not None and selected_id != loaded_id:
            swaps += 1

        loaded_id = selected_id

    return swaps


def main() -> None:
    with_bonus = RoutingPolicy()
    without_bonus = RoutingPolicy(loaded_bonus_weight=0.0)

    swaps_with_bonus = _simulate(with_bonus)
    swaps_without_bonus = _simulate(without_bonus)

    print("=" * 60)
    print("I-05 Single-Slot Scheduler -- swap count simulation")
    print("=" * 60)
    print(f"Requests simulated:        {len(PROMPTS)}")
    print(f"Swaps WITHOUT sticky bonus: {swaps_without_bonus}")
    print(f"Swaps WITH sticky bonus:    {swaps_with_bonus}")

    if swaps_with_bonus < swaps_without_bonus:
        print("\nResult: sticky bonus reduced swap count.")
    elif swaps_with_bonus == swaps_without_bonus:
        print("\nResult: no change for this workload (already minimal swapping).")
    else:
        print("\nResult: UNEXPECTED -- sticky bonus increased swaps.")


if __name__ == "__main__":
    main()
