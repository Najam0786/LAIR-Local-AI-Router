from app.capabilities.engine import engine
from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement
from app.hardware.filter import filter_by_hardware
from app.hardware.hardware_provider import HardwareProvider
from app.hardware.hardware_provider import hardware_provider as default_hardware_provider
from app.hardware.resource_resolver import ResourceResolver
from app.hardware.resource_resolver import resource_resolver as default_resource_resolver
from app.knowledge.knowledge_base import KnowledgeBase, default_knowledge_base
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.execution_plan import ExecutionPlan, ExecutionStep
from app.routing.policy import RoutingPolicy, default_policy
from app.routing.request_analyzer import analyzer
from app.routing.selector import selector


class RoutingEngine:
    """
    Core routing engine for LAIR.

    Converts a Task into capability requirements and selects
    the most appropriate AI model.
    """

    def route(
        self,
        task: Task,
        models: list[AIModel],
        policy: RoutingPolicy | None = None,
        knowledge_base: KnowledgeBase | None = None,
        hardware_provider: HardwareProvider | None = None,
        resource_resolver: ResourceResolver | None = None,
    ) -> ExecutionPlan:
        """
        Route a Task to the best matching model.
        """

        policy = policy or default_policy
        knowledge_base = (
            knowledge_base
            if knowledge_base is not None
            else default_knowledge_base
        )
        hardware_provider = (
            hardware_provider
            if hardware_provider is not None
            else default_hardware_provider
        )
        resource_resolver = (
            resource_resolver
            if resource_resolver is not None
            else default_resource_resolver
        )

        requirements: list[CapabilityRequirement] = (
            analyzer.analyze(task.prompt)
        )

        profiles: list[CapabilityProfile] = [
            model.profile
            for model in models
        ]

        matching_profiles = engine.find_matching_profiles(
            requirements=requirements,
            profiles=profiles,
        )

        matching_model_ids = {
            profile.model_id
            for profile in matching_profiles
        }

        candidate_models = [
            model
            for model in models
            if model.id in matching_model_ids
        ]

        candidate_models = [
            model
            for model in candidate_models
            if model.loaded
        ]

        resource_profiles = {
            model.id: resource_resolver.resolve(model.id, model.metadata)
            for model in candidate_models
        }

        hardware = hardware_provider.detect()

        candidate_models = filter_by_hardware(
            candidate_models,
            resource_profiles,
            hardware,
        )

        decision = selector.select(
            task,
            candidate_models,
            requirements,
            policy,
            knowledge_base,
        )

        step = ExecutionStep(
            role="primary",
            model_id=decision.selected_model.id,
            provider=decision.selected_model.provider,
        )

        return ExecutionPlan(
            steps=[step],
            decision=decision,
        )


routing_engine = RoutingEngine()
