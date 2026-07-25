import json
from pathlib import Path

from pydantic import BaseModel

from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase, default_knowledge_base

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_SNAPSHOT_PATH = _ROOT / "configs" / "community_scores" / "snapshot.json"


class CommunityScoreEntry(BaseModel):
    """
    One anonymized, community-contributed benchmark data point (I-12).
    Deliberately minimal -- hardware tier + model + score only, never a
    prompt or anything else that could identify a contributor or their
    usage, per the plan's own design notes.
    """

    model_id: str
    hardware_tier: HardwareTier
    tokens_per_second: float
    sample_count: int = 1


class CommunityScoreTable:
    """
    Read-only view over a static community score snapshot (I-12) --
    fetched from a GitHub repo snapshot file, not a live server; no
    server infrastructure needed for this pass, per the plan's own
    "static JSON snapshots... no server infrastructure needed for v1."
    """

    def __init__(self, entries: list[CommunityScoreEntry]):
        self._entries = entries

    def for_model_and_tier(
        self, model_id: str, tier: HardwareTier
    ) -> CommunityScoreEntry | None:
        for entry in self._entries:
            if entry.model_id == model_id and entry.hardware_tier == tier:
                return entry

        return None


class CommunityScoreLoader:
    def __init__(self, path: Path | str = _DEFAULT_SNAPSHOT_PATH):
        self._path = Path(path)

    def load(self) -> CommunityScoreTable:
        if not self._path.exists():
            return CommunityScoreTable([])

        text = self._path.read_text(encoding="utf-8").strip()

        if not text:
            return CommunityScoreTable([])

        return CommunityScoreTable(
            [CommunityScoreEntry(**record) for record in json.loads(text)]
        )


def export_contribution(
    hardware_tier: HardwareTier, knowledge_base: KnowledgeBase | None = None
) -> str:
    """
    Produces a shareable, anonymized JSON export of this machine's own
    local benchmark results (I-12 acceptance criterion) -- model id,
    hardware tier, and measured tokens/sec only. Never includes the
    benchmark `prompt` or anything else `BenchmarkResult` carries
    beyond the score itself.
    """

    knowledge_base = knowledge_base or default_knowledge_base

    entries = [
        CommunityScoreEntry(
            model_id=result.model_id,
            hardware_tier=hardware_tier,
            tokens_per_second=result.tokens_per_second,
        )
        for result in knowledge_base.all_latest().values()
    ]

    return json.dumps(
        [json.loads(entry.model_dump_json()) for entry in entries],
        indent=2,
    )


community_score_loader = CommunityScoreLoader()
