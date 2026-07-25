from app.capabilities.requirement import CapabilityRequirement
from app.core.settings import settings
from app.hardware.filter import filter_by_hardware
from app.hardware.hardware_provider import HardwareProvider
from app.hardware.hardware_provider import hardware_provider as default_hardware_provider
from app.hardware.power import read_power_state
from app.hardware.resource_resolver import ResourceResolver
from app.hardware.resource_resolver import resource_resolver as default_resource_resolver
from app.knowledge.knowledge_base import KnowledgeBase, default_knowledge_base
from app.models.ai_model import AIModel
from app.models.task import Task
from app.registry.community_scores import CommunityScoreTable, community_score_loader
from app.registry.portfolio import default_portfolio_store
from app.routing.complexity import ComplexityAssessment, complexity_triage
from app.routing.execution_plan import ExecutionPlan, ExecutionStep
from app.routing.language import detect_language
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
        complexity_override: ComplexityAssessment | None = None,
        community_scores: CommunityScoreTable | None = None,
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

        # A model-assisted classification (I-04 Phase 2), when supplied,
        # takes priority over the Phase 1 rules -- computed by the
        # caller (see app/api/chat.py), never by this method: the
        # routing engine itself never performs inference (CLAUDE.md's
        # routing principle), only decides who does.
        complexity: ComplexityAssessment | None = complexity_override or (
            complexity_triage.assess(task.prompt, task.conversation_turns)
            if settings.ENABLE_COMPLEXITY_TRIAGE
            else None
        )

        language_code: str | None = (
            detect_language(task.prompt)
            if settings.ENABLE_LANGUAGE_ROUTING
            else None
        )

        candidate_models = models

        hardware = hardware_provider.detect()

        resource_profiles = {
            model.id: resource_resolver.resolve(
                model.id,
                model.metadata,
                model.profile.context_window,
                hardware.available_ram_gb,
            )
            for model in candidate_models
        }

        # I-12/I-16: the tier and streaming_viability used below come
        # from whatever `lair doctor --init` last recorded, not
        # re-derived per request -- GPU/SSD detection are deliberately
        # not run on this hot path (LocalHardwareProvider always
        # reports gpu_vram_gb as unknown; see its own docstring), so a
        # fresh per-request guess would misclassify every GPU-having
        # machine as CPU_ONLY. No saved portfolio means no community
        # fallback and no streaming allowance, not a guessed one.
        active_portfolio = default_portfolio_store.load()
        hardware_tier = active_portfolio.tier if active_portfolio else None
        streaming_viability = (
            active_portfolio.streaming_viability if active_portfolio else None
        )

        candidate_models = filter_by_hardware(
            candidate_models,
            resource_profiles,
            hardware,
            streaming_viability=streaming_viability,
        )

        community_scores = (
            community_scores
            if community_scores is not None
            else community_score_loader.load()
        )

        power_state = (
            read_power_state() if settings.ENABLE_BATTERY_AWARENESS else None
        )

        decision = selector.select(
            task,
            candidate_models,
            requirements,
            policy,
            knowledge_base,
            complexity,
            resource_profiles,
            hardware,
            language_code,
            community_scores=community_scores,
            hardware_tier=hardware_tier,
            power_state=power_state,
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
