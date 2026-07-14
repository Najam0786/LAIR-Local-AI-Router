import json
from pathlib import Path
from threading import Lock

from app.routing.decision import DecisionRecord

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "logs" / "decisions.json"


class DecisionRepository:
    """
    Append-only log of routing decisions.

    Written by the Decision Engine after every decision; read by the
    future Learning Engine and audit/dashboard tooling -- never read
    by the Decision Engine itself.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._lock = Lock()

    def record(self, decision: DecisionRecord) -> None:
        with self._lock:
            records = self._read_all()
            records.append(json.loads(decision.model_dump_json()))

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

    def all(self) -> list[DecisionRecord]:
        return [DecisionRecord(**record) for record in self._read_all()]


default_decision_repository = DecisionRepository()
