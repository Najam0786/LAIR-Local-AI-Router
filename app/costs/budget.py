import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.core.settings import settings

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "logs" / "cloud_budget.json"


class CloudBudgetLedger:
    """
    Append-only log of real cloud-API spend (I-06, RFC-0001).

    Deliberately separate from `SavingsLedger`: that tracks money
    *not* spent (an informational, always-non-negative estimate);
    this tracks money *actually* spent against a hard monthly cap that
    must never be silently exceeded. Conflating the two in one object
    risks a bug in one corrupting the other's meaning. Same JSON-backed,
    lock-guarded pattern as every other store in this codebase.
    """

    def __init__(
        self,
        monthly_budget_usd: float | None = None,
        path: Path | str = _DEFAULT_PATH,
    ):
        # An explicit budget is fixed for this ledger's lifetime
        # (tests rely on this). Omitting it reads Settings live on
        # every check instead of snapshotting it once at construction
        # -- a ledger built before the caller configures the budget
        # (e.g. this codebase's autouse test fixture, built before a
        # test's own monkeypatch runs) must still see the real value.
        self._monthly_budget_usd_override = monthly_budget_usd
        self._path = Path(path)
        self._lock = Lock()

    @property
    def _monthly_budget_usd(self) -> float:
        if self._monthly_budget_usd_override is not None:
            return self._monthly_budget_usd_override

        return settings.CLOUD_MONTHLY_BUDGET_USD

    def record(self, usd: float) -> None:
        with self._lock:
            records = self._read_all()
            records.append(
                {
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
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

    def spent_this_month(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        total = 0.0

        for record in self._read_all():
            recorded_at = datetime.fromisoformat(record["recorded_at"])

            if (recorded_at.year, recorded_at.month) == (now.year, now.month):
                total += record.get("usd", 0.0)

        return round(total, 6)

    def remaining_this_month(self, now: datetime | None = None) -> float:
        return max(0.0, self._monthly_budget_usd - self.spent_this_month(now))


default_cloud_budget_ledger = CloudBudgetLedger()
