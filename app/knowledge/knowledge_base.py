import json
import logging
from pathlib import Path
from threading import Lock

from pydantic import ValidationError

from app.benchmarking.benchmark_result import BenchmarkResult

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "benchmarks" / "knowledge_base.json"


class KnowledgeBase:
    """
    Queryable store of benchmark results.

    Read-only from the Decision Engine and scorers; written only
    by the Benchmark Engine (and, later, the Learning Engine and
    provider health monitors) — see ADR-0006.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._lock = Lock()

    def record(self, result: BenchmarkResult) -> None:
        with self._lock:
            records = self._read_all()
            records.append(json.loads(result.model_dump_json()))

            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(records, indent=2),
                encoding="utf-8",
            )

    def _read_all(self) -> list[dict]:
        if not self._path.exists():
            return []

        text = self._path.read_text(encoding="utf-8").strip()

        return json.loads(text) if text else []

    def _parse(self, record: dict) -> BenchmarkResult | None:
        try:
            return BenchmarkResult(**record)
        except ValidationError as exc:
            logger.warning(
                "Skipping unreadable benchmark record for %s: %s",
                record.get("model_id", "<unknown>"),
                exc,
            )
            return None

    def latest(self, model_id: str) -> BenchmarkResult | None:
        matches = [
            result
            for result in (
                self._parse(record)
                for record in self._read_all()
                if record.get("model_id") == model_id
            )
            if result is not None
        ]

        if not matches:
            return None

        return max(matches, key=lambda result: result.measured_at)

    def all_latest(self) -> dict[str, BenchmarkResult]:
        latest: dict[str, BenchmarkResult] = {}

        for record in self._read_all():
            result = self._parse(record)

            if result is None:
                continue

            existing = latest.get(result.model_id)

            if existing is None or result.measured_at > existing.measured_at:
                latest[result.model_id] = result

        return latest


default_knowledge_base = KnowledgeBase()
