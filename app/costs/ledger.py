import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.schemas.savings import SavingsTotals

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "logs" / "savings.json"


class SavingsLedger:
    """
    Append-only log of estimated cloud-cost savings per request.

    Mirrors DecisionRepository/KnowledgeBase's JSON-backed, lock-guarded
    pattern (ADR-0005/ADR-0010) rather than introducing a new storage
    mechanism.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._lock = Lock()

    def record(self, model_id: str, usd: float) -> None:
        with self._lock:
            records = self._read_all()
            records.append(
                {
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "model_id": model_id,
                    "usd": usd,
                }
            )

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

    def totals(self, now: datetime | None = None) -> SavingsTotals:
        now = now or datetime.now(timezone.utc)

        day_total = 0.0
        month_total = 0.0
        lifetime_total = 0.0

        for record in self._read_all():
            usd = record.get("usd", 0.0)
            lifetime_total += usd

            recorded_at = datetime.fromisoformat(record["recorded_at"])

            if recorded_at.date() == now.date():
                day_total += usd

            if (recorded_at.year, recorded_at.month) == (now.year, now.month):
                month_total += usd

        return SavingsTotals(
            day_usd=round(day_total, 6),
            month_usd=round(month_total, 6),
            lifetime_usd=round(lifetime_total, 6),
        )


default_savings_ledger = SavingsLedger()
