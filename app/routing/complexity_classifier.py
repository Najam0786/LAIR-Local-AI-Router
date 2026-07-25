import hashlib
import json
import logging
import re
import time
from pathlib import Path
from threading import Lock

from pydantic import BaseModel

from app.core.settings import settings
from app.registry.provider_registry import ProviderRegistry
from app.registry.provider_registry import provider_registry as _default_registry
from app.routing.complexity import MAX_COMPLEXITY, MIN_COMPLEXITY, ComplexityAssessment

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CACHE_PATH = _ROOT / "logs" / "complexity_classifications.json"

_CLASSIFICATION_PROMPT_TEMPLATE = (
    "Rate the complexity of the following user request on a scale of "
    "1 (trivial) to 5 (hard) and name its task type in a few words. "
    'Respond with ONLY JSON, no other text: {{"complexity": <1-5>, '
    '"task_type": "<type>"}}.\n\nRequest: {prompt}'
)

_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


class _ClassificationCacheEntry(BaseModel):
    level: int
    task_type: str
    classified_at: float


class ClassificationCache:
    """
    Caches model-assisted complexity classifications by prompt hash
    (I-04 Phase 2) -- every cache hit avoids a real inference call, the
    entire point of caching a classification instead of re-asking the
    model each time. Same JSON-backed, lock-guarded pattern as
    ResponseCache/KnowledgeBase/DecisionRepository/SavingsLedger.
    """

    def __init__(
        self,
        ttl_seconds: int | None = None,
        path: Path | str = _DEFAULT_CACHE_PATH,
    ):
        self._ttl_seconds = (
            ttl_seconds
            if ttl_seconds is not None
            else settings.COMPLEXITY_CLASSIFICATION_CACHE_TTL_SECONDS
        )
        self._path = Path(path)
        self._lock = Lock()

    @staticmethod
    def key_for(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def get(self, key: str) -> _ClassificationCacheEntry | None:
        with self._lock:
            records = self._read_all()
            record = records.get(key)

            if record is None:
                return None

            entry = _ClassificationCacheEntry(**record)

            if time.time() - entry.classified_at > self._ttl_seconds:
                return None

            return entry

    def put(self, key: str, level: int, task_type: str) -> None:
        with self._lock:
            records = self._read_all()
            records[key] = {
                "level": level,
                "task_type": task_type,
                "classified_at": time.time(),
            }

            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def _read_all(self) -> dict:
        if not self._path.exists():
            return {}

        text = self._path.read_text(encoding="utf-8").strip()

        if not text:
            return {}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}


default_classification_cache = ClassificationCache()


class ModelAssistedComplexityClassifier:
    """
    I-04 Phase 2: asks a designated fast local model to rate a
    request's complexity, instead of (or as a supplement to) the
    Phase 1 rules-based ComplexityTriage.

    Deliberately lives outside RoutingEngine -- the routing engine
    itself never performs inference, only decides who does (CLAUDE.md's
    routing principle). This classifier runs at the API layer *before*
    routing, and its result is passed into RoutingEngine.route() as a
    plain value; the routing engine stays a pure computation either way.

    Off by default (Settings.ENABLE_MODEL_ASSISTED_COMPLEXITY) --  every
    uncached call is a real inference round-trip, a real latency and
    compute cost Phase 1's rules aren't.
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry = _default_registry,
        cache: ClassificationCache | None = None,
    ):
        self._provider_registry = provider_registry
        self._cache = cache or default_classification_cache

    async def classify(self, prompt: str) -> ComplexityAssessment | None:
        """
        Returns a model-assisted ComplexityAssessment, or None if the
        feature is disabled, unconfigured, or the classifier call
        fails for any reason -- callers should fall back to the Phase 1
        heuristic, never treat this as a hard requirement.
        """

        if not settings.ENABLE_MODEL_ASSISTED_COMPLEXITY:
            return None

        model_id = settings.COMPLEXITY_CLASSIFIER_MODEL_ID

        if not model_id:
            return None

        cache_key = self._cache.key_for(prompt)
        cached = self._cache.get(cache_key)

        if cached is not None:
            return self._to_assessment(cached.level, cached.task_type, from_cache=True)

        models = await self._provider_registry.list_models()
        model = next((m for m in models if m.id == model_id), None)

        if model is None:
            logger.warning(
                "Complexity classifier model '%s' not found among "
                "available models; falling back to rules-based triage.",
                model_id,
            )
            return None

        try:
            provider = self._provider_registry.get(model.provider)
            result = await provider.complete(
                model.id,
                [
                    {
                        "role": "user",
                        "content": _CLASSIFICATION_PROMPT_TEMPLATE.format(
                            prompt=prompt
                        ),
                    }
                ],
                max_tokens=50,
            )
            level, task_type = self._parse(result.text)
        except Exception as exc:
            logger.warning(
                "Model-assisted complexity classification failed, "
                "falling back to rules-based triage: %s",
                exc,
            )
            return None

        if level is None:
            return None

        self._cache.put(cache_key, level, task_type)

        return self._to_assessment(level, task_type, from_cache=False)

    def _parse(self, text: str) -> tuple[int | None, str]:
        match = _JSON_OBJECT_PATTERN.search(text)

        if not match:
            return None, ""

        try:
            data = json.loads(match.group(0))
            level = int(data["complexity"])
            task_type = str(data.get("task_type", ""))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None, ""

        level = max(MIN_COMPLEXITY, min(MAX_COMPLEXITY, level))

        return level, task_type

    def _to_assessment(
        self, level: int, task_type: str, from_cache: bool
    ) -> ComplexityAssessment:
        suffix = " (cached)" if from_cache else ""
        task_note = f", task_type={task_type}" if task_type else ""

        return ComplexityAssessment(
            level=level,
            reasons=[f"Model-assisted classification{task_note}{suffix}"],
        )


default_complexity_classifier = ModelAssistedComplexityClassifier()
